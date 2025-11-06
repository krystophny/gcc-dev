# Outstanding Issues After Deep-Copy Patch

This note tracks the two regressions we exposed while testing the deep-copy
work and records repro instructions plus tentative fixes.

## 1. Recursive type self-copy ICE (structure_alloc_comps)

**Symptoms.** `gfortran` trunk now segfaults in
`gfc_build_addr_expr()` while lowering the default assignment helper for a
type that owns two allocatable components of the same derived type. Reproducer
is checked in at `bugs/pr121628/minimal_bug.f90`:

```fortran
program minimal_bug
  implicit none
  type :: nested_t
     type(nested_t), allocatable :: children(:)
     type(nested_t), allocatable :: relatives(:)
  end type nested_t
  type(nested_t) :: a
end program minimal_bug
```

Build/run commands (from repo root):

```bash
make -C gcc-build -j$(nproc)
./gcc-build/gcc/gfortran \
  -B ./gcc-build/gcc \
  -L ./gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
  -Wl,-rpath,$PWD/gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
  -c bugs/pr121628/minimal_bug.f90
```

Expected: successful compile. Actual: stack reports repeated recursion into
`structure_alloc_comps`, ending in `gfc_build_addr_expr`. GCC 15.2.1 compiles
it fine.

**Root cause.** In our new branch

```c
else if (c->attr.allocatable && c->as ... && same_type && purpose == COPY_ALLOC_COMP)
```

we call `_gfortran_cfi_deep_copy_array` even when `decl == dest`. During
intrinsic-assignment generation (`__copy_*` helper) both point at the same
synthetic descriptor, so we end up taking the address of a non-component node
and blow up.

**Fix approach.** Guard the branch so it only fires when we are actually working
with two distinct component references, e.g.

```c
else if (dest
         && TREE_CODE (dcmp) == COMPONENT_REF
         && TREE_CODE (comp) == COMPONENT_REF
         && decl != dest
         && ...)
```

This skips the runtime helper while we’re still emitting the default copy
routine, preventing the infinite descent. Needs validation to ensure it still
handles the real recursive copies.

## 2. FINAL + recursive allocatable ICE (gimplify_call_expr)

**Symptoms.** Both trunk and GCC 15.2.1 ICE during the gimplifier when a type
with a FINAL procedure owns recursive allocatable components. Minimal driver is
under `bugs/finalizer-ice/finalizer_min.f90`. Build with our tree:

```bash
./gcc-build/gcc/gfortran \
  -B ./gcc-build/gcc \
  -L ./gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
  -Wl,-rpath,$PWD/gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
  -o finalizer_min.x bugs/finalizer-ice/finalizer_min.f90
```

Expected: compile+run succeeds; actual: ICE in `gimplify_call_expr` (tree check
for function/method type fails). Intel ifx 2025.2.1 handles it, so it’s a GCC
front-end regression unrelated to our runtime helper.

**Next steps.** Once the guard above is in place, this program reaches the same
ICE as before and should be filed as a separate Bugzilla entry (the repro is
already staged in the repo). Needs deeper gimplifier work, likely independent of
our patch.
