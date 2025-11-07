# GCC PR103368 - ICE with class(*) in structure constructor

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103368
**Status:** RESOLVED FIXED
**Title:** [11/12/13 Regression] ICE in gimplify_expr, at gimplify.c:15668

## Description

This bug triggers an internal compiler error when passing a structure constructor
containing a class(*) component to a subroutine. The code is actually valid - Intel
and NAG compilers accept it - but earlier GCC versions produced an ICE.

## Expected Behavior

Valid Fortran code with class(*) allocatable components should compile cleanly.

## Actual Behavior

- GCC 11-13: ICE in gimplify_expr at gimplify.c:15668
- GCC 14+: Fixed

## Test Results

### System gfortran (GNU Fortran 15.2.1)
- Status: PASS
- Compiles and links without errors

### Dev gfortran (gcc-build/gcc/gfortran)
- Status: PASS
- Compiles and links without errors

### Intel ifx 2025.2.1
- Status: PASS
- Compiles and links without errors

## Reproducer

See `reproducer.f90` - structure constructor with class(*) component.

## Fix Details

The issue was substantially resolved in GCC 14-branch through unrelated fixes.
The maintainer closed the issue without a specific fix, noting that other compiler
changes resolved the problem.
