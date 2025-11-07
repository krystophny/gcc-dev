# GCC PR113885 - ICE with finalization and elemental functions

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=113885
**Status:** RESOLVED FIXED
**Title:** [13 Regression] ice in gimplify_expr, at gimplify.cc:18658 with finalization

## Description

This bug triggers an internal compiler error when using elemental functions with
finalization on zero-component derived types. The ICE occurs during gimplification
when processing elemental assignments involving types with final procedures.

## Expected Behavior

The code should compile cleanly. The issue was a regression where finalization
blocks were incorrectly placed relative to right-hand-side post-block evaluation
during elemental operations.

## Actual Behavior

- GCC 13.2.1 - 14.0: ICE in gimplify_expr at gimplify.cc:18658
- GCC 15+: Fixed

## Test Results

### System gfortran (GNU Fortran 15.2.1)
- Status: PASS
- Compiles without errors

### Dev gfortran (gcc-build/gcc/gfortran)
- Status: PASS
- Compiles without errors

### Intel ifx 2025.2.1
- Status: PASS
- Compiles without errors

## Reproducer

See `reproducer.f90` - minimal test case with elemental function and finalizer.

## Fix Details

Paul Thomas fixed this by modifying finalization block placement in `trans-expr.cc`
and improving component detection logic in `trans.cc`. The fix was applied to both
master and release branches by May 2024.
