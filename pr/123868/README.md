# Bug 123868: Memory leak on assignment with nested allocatable components

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123868
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/47
- **Status:** MERGED (gcc commit ca448bc5e435)

## Summary

Memory leak occurs when assigning derived types containing allocatable array
components where the array element type also has allocatable components. This
is a regression introduced in GCC 16 by commit 9636d90e4326003e6da1ea86df7c730852629920
(PR121628).

## Reproducer

```fortran
module bugMod
  type :: vs
     character(len=1), allocatable :: s
  end type vs

  type :: ih
     type(vs), allocatable, dimension(:) :: hk
  end type ih
end module bugMod

program bugProg
  use bugMod
  block
    type(ih) :: c, d
    allocate(d%hk(1))
    allocate(d%hk(1)%s)
    d%hk(1)%s='z'
    c=d              ! <-- leak occurs here (8 bytes)
    write (*,*) c%hk(1)%s,d%hk(1)%s
  end block
end program bugProg
```

## Valgrind Output (Before Fix)

```
==260290== HEAP SUMMARY:
==260290==     in use at exit: 8 bytes in 1 blocks
==260290==   total heap usage: 22 allocs, 21 frees, 5,510 bytes allocated
==260290==
==260290== 8 bytes in 1 blocks are definitely lost in loss record 1 of 1
==260290==    at 0x4844818: malloc (vg_replace_malloc.c:446)
==260290==    by 0x40239D: MAIN__ (reproducer.f90:26)
==260290==    by 0x402823: main (reproducer.f90:18)
```

## Valgrind Output (After Fix)

```
==267336== HEAP SUMMARY:
==267336==     in use at exit: 0 bytes in 0 blocks
==267336==   total heap usage: 21 allocs, 21 frees, 5,502 bytes allocated
==267336==
==267336== All heap blocks were freed -- no leaks are possible
```

## Root Cause Analysis

### Regression caused by

Commit `9636d90e4326003e6da1ea86df7c730852629920` (PR121628) which implemented
deep copy semantics for recursive allocatable array components. The commit
changed the condition in `structure_alloc_comps()` that determines when to
call `gfc_duplicate_allocatable()`.

### Technical Details

In `gcc/fortran/trans-array.cc`, the `structure_alloc_comps()` function handles
the COPY_ALLOC_COMP case for derived type assignment. For allocatable components
with nested allocatable components, the code generates deep copy logic in two
places:

1. **Lines 10968-10978**: Generates `add_when_allocated` by recursively calling
   `structure_alloc_comps()`. For allocatable ARRAY components, this recursive
   call (at lines 10290-10293) wraps the element deep-copy loop inside a
   `gfc_duplicate_allocatable()` call, which allocates the outer array.

2. **Lines 11066-11097**: Conditionally calls `gfc_duplicate_allocatable()`
   again with `add_when_allocated` as the deep-copy code.

The OLD condition at line 11066 was:
```c
else if (c->attr.allocatable && !c->attr.proc_pointer
         && (!(cmp_has_alloc_comps && c->as) || c->attr.codimension
             || caf_in_coarray (caf_mode)))
```

For allocatable arrays with nested allocatables (`cmp_has_alloc_comps && c->as`),
this evaluated to FALSE, causing the code to fall through to line 11100 which
simply adds `add_when_allocated` (which already contains the allocation).

The NEW condition changed this to:
```c
else if (c->attr.allocatable && !c->attr.proc_pointer
         && (add_when_allocated != NULL_TREE
             || !cmp_has_alloc_comps
             || !c->as
             || c->attr.codimension
             || caf_in_coarray (caf_mode)))
```

The addition of `add_when_allocated != NULL_TREE` causes allocatable arrays
with nested allocatables to enter this branch, calling `gfc_duplicate_allocatable()`
even though `add_when_allocated` already contains such a call.

### Generated Code (Bug)

The tree dump shows DOUBLE ALLOCATION:
```c
c.hk = d.hk;  // descriptor copy
if ((void *) d.hk.data != 0B) {
    D.4929 = __builtin_malloc(...);     // First allocation (M1)
    c.hk.data = D.4929;
    __builtin_memcpy(c.hk.data, d.hk.data, ...);
    if ((void *) d.hk.data != 0B) {
        D.4926 = __builtin_malloc(...); // Second allocation (M2) - M1 leaked!
        c.hk.data = D.4926;             // Overwrites M1 pointer
        __builtin_memcpy(c.hk.data, d.hk.data, ...);
        // ... deep copy loop for nested s component
    }
}
```

### Generated Code (Fixed)

After fix, only ONE allocation:
```c
c.hk = d.hk;  // descriptor copy
if ((void *) d.hk.data != 0B) {
    D.4923 = __builtin_malloc(...);     // Single allocation
    c.hk.data = D.4923;
    __builtin_memcpy(c.hk.data, d.hk.data, ...);
    // ... deep copy loop for nested s component (no extra allocation)
}
```

## The Fix

The fix limits `add_when_allocated != NULL_TREE` to scalar allocatables only
(`!c->as`), restoring the OLD behavior for array components:

```c
else if (c->attr.allocatable && !c->attr.proc_pointer
         && ((add_when_allocated != NULL_TREE && !c->as)  // <-- Added && !c->as
             || !cmp_has_alloc_comps
             || !c->as
             || c->attr.codimension
             || caf_in_coarray (caf_mode)))
```

For allocatable arrays with nested allocatables, the code now falls through
to line 11100, which adds `add_when_allocated` directly (which already contains
the proper allocation code).

## Test Results

| Compiler | Memory Leak |
|----------|-------------|
| gfortran 15.2 | No |
| gfortran 14.x | No |
| ifort | No |
| gfortran 16 (before fix) | **Yes - 8 bytes** |
| gfortran 16 (after fix) | **No** |

## Files Changed

- `gcc/fortran/trans-array.cc`: Fix condition at line 11066-11071
- `gcc/testsuite/gfortran.dg/pr123868.f90`: New test case
