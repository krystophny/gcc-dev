# GCC PR85002 - Coarray ICE in fold_ternary_loc

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85002
**Status:** RESOLVED FIXED
**Title:** [12/13/14/15 Regression][Coarray] ICE in fold_ternary_loc, at fold-const.c:11360

## Description

This bug triggers an internal compiler error when compiling Fortran code involving
coarrays with allocatable components in derived types. The compiler crashes during
code generation when trying to perform deep copies of nested allocatable structures
in coarray assignments.

## Expected Behavior

Coarray assignments with allocatable components should compile cleanly with
`-fcoarray=single`.

## Actual Behavior

- GCC 12-15: ICE in fold_ternary_loc at fold-const.c:11360
- GCC 16+: Fixed

## Test Results

### System gfortran (GNU Fortran 15.2.1)
- Status: PASS
- Compiles with -fcoarray=single without errors

### Dev gfortran (gcc-build/gcc/gfortran)
- Status: PASS
- Compiles with -fcoarray=single without errors

### Intel ifx
- Status: SKIP (not installed)

## Reproducer

See `reproducer.f90` - minimal coarray test with allocatable component.
Must compile with `-fcoarray=single`.

## Fix Details

Fixed on September 19, 2024, addressing issues in how allocatable components
undergo deep copying in coarray contexts. The patch ensures proper code generation
and bounds computation for coarray assignments involving nested derived types.
