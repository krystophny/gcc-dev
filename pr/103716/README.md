# GCC PR103716 - ICE with character len inquiry

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103716
**Status:** RESOLVED FIXED
**Title:** [11/12/13 Regression] ICE in gimplify_expr, at gimplify.c:15964

## Description

This bug triggers an internal compiler error when using the `%len` inquiry on
assumed-length character arrays. The compiler crashes during gimplification
rather than properly handling the length inquiry syntax.

## Expected Behavior

The `%len` inquiry should work correctly on assumed-length character variables
within array contexts.

## Actual Behavior

- GCC 11-13: ICE in gimplify_expr at gimplify.c:15964
- GCC 14+: Fixed

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

See `reproducer.f90` - character length inquiry test.

## Fix Details

Paul Thomas fixed this issue in May 2023 through changes to `resolve.cc` and
`trans-expr.cc` in the Fortran frontend, ensuring proper handling of character
length inquiries. The fix was backported to GCC 12, 13, and 14 branches.
