# Bug 125113: shmem CAF segfault on coindexed access through pointer component

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=125113
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/168
- **Reporter:** Neil Carlson (`neil.n.carlson`)
- **Status:** NEW, P3, normal severity, gfortran 17.0
- **Severity (local):** runtime-crash on valid (or marginally valid) code,
  shmem CAF runtime only.
- **Component scope:** Fortran front end (`gcc/fortran/coarray.cc`) and
  `libgfortran/caf/shmem.c` + `libgfortran/caf/shmem/`. No other GCC
  subsystem involved.
- **Fix status:** triaged, analysis-only. No patch posted; the clean fix is
  architectural (see below).

## Symptom

Two-image program with a coarray of derived type that has a `pointer`
component, where the component is `=>`-assigned to a non-coarray local
target. Coindexed access from another image segfaults inside the
generated `_caf_accessor_*` accessor function.

The reduced reproducer in `reproducer.f90` is:

```fortran
type :: box
  integer, pointer :: data(:) => null()
end type
type(box), allocatable :: buffer[:]
integer, allocatable, target :: src(:)
...
allocate(buffer[*])
buffer%data => src                ! pointer assignment, target is local heap
sync all
dest = buffer[1]%data(first_gid:last_gid)   ! SIGSEGV in accessor
```

`gfortran -fcoarray=lib pr125113.f90 -lcaf_shmem`, run with
`GFORTRAN_NUM_IMAGES=2`. Fault stack:

```
#1  0x...  in _caf_accessor_main_buffer_1
#2  0x...  in pr125113
#3  0x...  in main
ERROR: Image 2(pid: ...) failed with signal 11, exitstatus 0.
```

The same code compiles and runs cleanly with gfortran 13.3 + opencoarrays,
which is why the reporter labels it a regression from 13.3.

## Empirical confirmation

A diagnostic build that prints `loc(buffer)` and `loc(buffer%data)` on each
image yields, on this host:

```
img 1: loc(src)=        3B23E8A0 size=4
img 1: loc(buffer)=    7EF95E200EC0 loc(buffer%data)=        3B23E8A0
img 2: loc(src)=        2FDCD860 size=0
img 2: loc(buffer)=    7EF95E200F20 loc(buffer%data)=        2FDCD860
img 2 about to fetch from img 1 ...
SIGSEGV
```

`loc(buffer)` differs between images by `0x60` bytes: image-2's slot
inside the shared-memory region. Both addresses live in the
`0x7EF9...` range characteristic of the shmem mmap. `loc(buffer%data)`
on image 1 is `0x3B23E8A0`, image 1's local heap (allocator output for
`src`). Image 2's accessor reads image 1's slot, finds
`buffer.data.data == 0x3B23E8A0`, and dereferences that pointer in
image-2's address space, where the page is unmapped.

## Root cause

The new shmem CAF runtime in libgfortran combines two design choices that
produce a hidden invariant:

1. Every image `mmap`s the shared memory region at the same virtual
   address (`libgfortran/caf/shmem/shared_memory.c`, the master image
   stashes its base in `GFORTRAN_SHMEM_BASE` and other images mmap with
   that as `addr` hint, exiting 210 to retry on mismatch). Consequence: a
   pointer into shmem from any image is also a valid pointer in any
   other image.
2. Coindexed read accessors are invoked **directly in the caller's
   process** (`libgfortran/caf/shmem.c:_gfortran_caf_get_from_remote`,
   line ~1088, with `src_ptr = shmem_token->base + remote_image_index *
   shmem_token->image_size`). No fork, no IPC, no signal-based
   delegation.

The combined invariant: anything reachable from the remote slot must
itself live inside the shmem region. The invariant holds for:

- the coarray itself (allocated through the shmem allocator);
- allocatable components of coarray-derived-types (the runtime allocator
  routes through the shmem allocator since the parent is a shmem
  coarray);
- pointer components targeting other coarrays (those targets are also in
  shmem).

The invariant is silently violated when a pointer component is
`=>`-assigned to a non-coarray local target (a regular `target`
allocatable, a regular local variable, or a function-local pointee).
That target is in per-image private heap; image 1's pointer value is not
a valid address in image 2's process. The accessor compiles into

```
D.4782 = (integer(kind=4)[0:] *) buffer->data.data;       /* read shmem */
... = *((integer(kind=4) *) D.4782 + ...);                /* deref local heap, SIGV */
```

The tree dump shows this shape in the generated accessor.

## Why no clever small fix

- Cannot rewrite `=>` to copy `src` into shmem: that breaks pointer
  semantics (mutations to `src` would no longer be visible through the
  pointer).
- Cannot translate the address at accessor time: the bytes simply aren't
  reachable from the caller's process. There is nothing to translate to.
- Cannot reliably diagnose at compile time: the target of `=>` is in
  general dynamic; the same source could legally point at a coarray on
  one path and at a local allocatable on another.
- A runtime range-check inside the accessor (verify
  `buffer->data.data` lies inside the shmem region before dereferencing)
  converts SIGSEGV into a clean `caf_runtime_error` but does not make
  any previously-broken program work.

## How this regression arose

Introduced when the shmem CAF runtime landed in
`c66d1ba685b "Fortran: Add a shared memory multi process coarray
implementation [PR88076]"` (Vehreschild). Subsequent commits extended
the same direct-call accessor model
(`{15847252648,69eb02682b8,8bf0ee8d62b,baa9b2b8d2e,8f4ee36bd52,
ee31ab9b195,fc029f5d341,ede3dd56e63,fee68dd1b48}`. See
`gcc/fortran/coarray.cc` history).

The gap survived review because no test in
`gcc/testsuite/gfortran.dg/coarray/ptr_comp_*.f08` combines the bug's
two ingredients:

- `ptr_comp_2.f08`, `ptr_comp_3.f08`: pointer component on a coarray,
  but the target is also a coarray → in shmem → works.
- `ptr_comp_4.f08`, `ptr_comp_5.f08`, `ptr_comp_6.f08`: no coindexed
  access → no remote accessor → no fault.

Opencoarrays (the older default CAF runtime) hid the bug for users on
gfortran 13.3 because its remote-fetch path RPCs the accessor to the
*source* image's process, where the local pointer is naturally valid.
The shmem implementation traded that RPC for a same-process accessor
to avoid IPC cost; that trade implicitly took the "everything reachable
must be in shmem" invariant on board.

## Fix paths

### Real fix (large)

Have the shmem runtime evaluate accessors on the source image's
process when the accessor body may dereference pointer components.
Requires either fork-on-demand or a long-lived worker thread per image
plus a request/response channel. Substantial change to `shmem.c`,
`shmem/supervisor.c`, and the codegen contract.

### Interim improvement (medium)

Two complementary front-end / runtime additions:

1. In `coarray.cc` accessor codegen, when the post-coarray-ref expression
   walks through a `pointer` (not allocatable) component, mark the
   accessor and emit a runtime range-check that aborts with
   `caf_runtime_error` ("pointer component target not in
   coarray-accessible memory; pointer-assigning a non-coarray target
   yields undefined behaviour under shmem CAF"). Replaces SIGSEGV with
   a diagnosable runtime error; doesn't make the user's program work.
2. Document the constraint in the gfortran manual (CAF section): under
   shmem CAF, pointer components of coarray-derived-types must target
   coarray-allocated memory if they will be read remotely.

### Compile-time hint (small)

At `=>` resolution time, when the LHS is a pointer component of a
coarray and the RHS is statically a non-coarray local target, emit a
warning. This catches the obvious cases (the testcase here) without
runtime cost.

## Files in this directory

- `reproducer.f90`: minimal reduction of the reporter's testcase,
  rewritten by hand. No verbatim Bugzilla code; the reporter's structure
  was kept (a coarray box wrapping a pointer to a local target array is
  the entire point of the bug), but variable names and surrounding flow
  were changed where doing so did not destroy the trigger.
- `README.md`: this file.
- `status.json`: machine-readable triage record.
