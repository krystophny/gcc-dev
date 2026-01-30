# Bug 123868: Memory leak on assignment with nested allocatable components

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123868
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/47
- **Status:** NEW (regression in GCC 16)

## Summary

Memory leak occurs when assigning derived types containing allocatable array
components where the array element type also has allocatable components. This
is a regression introduced in GCC 16.

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
    c=d              ! <-- leak occurs here
    write (*,*) c%hk(1)%s,d%hk(1)%s
  end block
end program bugProg
```

## Analysis

### Regression caused by

Commit 9636d90e4326003e6da1ea86df7c730852629920 (PR121628) which implemented
deep copy semantics for recursive allocatable array components.

### Key observations

1. **Not a recursive type issue**: Per Paul Thomas (Comment 4), the new
   recursive wrapper code path is NOT being triggered for this testcase
   because the types are not recursive (vs is not ih).

2. **Changed condition logic in trans-array.cc**: The commit modified the
   condition for the allocatable component handling branch:

   OLD:
   ```c
   else if (c->attr.allocatable && !c->attr.proc_pointer
            && (!(cmp_has_alloc_comps && c->as) || c->attr.codimension
                || caf_in_coarray (caf_mode)))
   ```

   NEW:
   ```c
   else if (c->attr.allocatable && !c->attr.proc_pointer
            && (add_when_allocated != NULL_TREE
                || !cmp_has_alloc_comps
                || !c->as
                || c->attr.codimension
                || caf_in_coarray (caf_mode)))
   ```

3. **The key difference**: When `add_when_allocated != NULL_TREE` (which is
   the case for allocatable array components with nested allocatables), the
   NEW code takes a different path that calls `gfc_duplicate_allocatable()`,
   while the OLD code fell through to just adding the deep copy code directly.

4. **Leak location**: Valgrind shows the leak at the assignment `c=d` (line 21),
   with 8 bytes (size of one allocatable character) leaked.

### Test results

| Compiler | Memory Leak |
|----------|-------------|
| gfortran 15.2 (Homebrew) | No |
| gfortran 14.x | No |
| ifort | No |
| gfortran 16.x (post-PR121628) | **Yes - 8 bytes** |

## Files involved

- `gcc/fortran/trans-array.cc`: structure_alloc_comps function (lines ~10968-11100)
- `libgfortran/runtime/deep_copy.c`: new runtime helper (not triggered for this case)

## Next steps

1. Build GCC 16 on Linux to confirm with valgrind
2. Add tree dump analysis to understand code generation differences
3. Identify precise fix location in structure_alloc_comps
