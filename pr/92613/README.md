# PR92613: Bogus warning with -cpp and -fpreprocessed

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=92613
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/7

**Component**: fortran

**Reported**: 2019-11-21 by Ignacio Fernández Galván

## Summary

When using `-cpp` and `-fpreprocessed` together, gfortran emits a bogus warning about a missing terminating quote character for quotes that appear inside comments.

## Reproducer

```fortran
program test
  implicit none
  write(6,*) 'hello'
! it's good!
end program
```

## Steps to Reproduce

```bash
gfortran -cpp reproducer.f90 -E -o reproducer.pp.f90
gfortran -cpp -fpreprocessed reproducer.pp.f90
```

## Expected Behavior

No warning should be emitted. The quote in `it's` is inside a comment and should not be treated as a string delimiter.

## Actual Behavior

```
reproducer.f90:4:5:

 ! it's good!
     1
Warning: missing terminating ' character
```

## Compiler Comparison (2024-12-04)

| Compiler | Version | Bogus Warning? |
|----------|---------|----------------|
| GCC (master) | 16.0.0 20251126 | YES - bug present |
| GCC (system) | 15.2.1 | YES - bug present |
| Intel ifx | 2025.2.1 | NO - compiles cleanly |
| NVIDIA nvfortran | 25.9 | NO - compiles cleanly |
| LFortran | latest | NO - compiles cleanly |

All other compilers handle `-cpp -fpreprocessed` (or equivalent flags) correctly without emitting warnings for quotes inside comments.

## Analysis

The preprocessor appears to be scanning comment text for string delimiters when `-cpp -fpreprocessed` is used together. This combination may occur when using build tools like CMake (see https://gitlab.kitware.com/cmake/cmake/issues/17466).

While using `-cpp` with `-fpreprocessed` may seem redundant, the warning is incorrect since the quote is part of a comment line and should be ignored entirely.

The bug is GCC-specific - all other major Fortran compilers handle this case correctly.

## Related

- CMake issue: https://gitlab.kitware.com/cmake/cmake/issues/17466

## Files

- `reproducer.f90` - Minimal reproducer
- `Makefile` - Build with multiple compilers
