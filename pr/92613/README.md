# PR92613: Bogus warning with -cpp and -fpreprocessed

**GCC Bugzilla**: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=92613

**Status**: NEW (unassigned)

**Component**: fortran

**Reported**: 2019-11-21 by Ignacio Fernández Galván

**Last Modified**: 2023-12-04

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

## Analysis

The preprocessor appears to be scanning comment text for string delimiters when `-cpp -fpreprocessed` is used together. This combination may occur when using build tools like CMake (see https://gitlab.kitware.com/cmake/cmake/issues/17466).

While using `-cpp` with `-fpreprocessed` may seem redundant, the warning is incorrect since the quote is part of a comment line and should be ignored entirely.

## Related

- CMake issue: https://gitlab.kitware.com/cmake/cmake/issues/17466

## Files

- `reproducer.f90` - Minimal reproducer
- `Makefile` - Build with multiple compilers
