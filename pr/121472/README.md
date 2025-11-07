# GCC PR121472 - ICE with constructor and finalizer

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
**Status:** UNCONFIRMED
**Title:** ICE in gimplify_expr

## Description

This bug triggers an internal compiler error when using a derived type with
both a final subroutine and a constructor interface. The assignment using
the constructor triggers the ICE during gimplification.

## Expected Behavior

Code using constructors and finalizers together should compile cleanly.

## Actual Behavior

- GCC 15.2.1: ICE in gimplify_expr at gimplify.cc:20443
- GCC 16.0 dev: ICE in gimplify_expr at gimplify.cc:21278
- Status: ACTIVE BUG - reproducible on current versions

## Test Results

### System gfortran (GNU Fortran 15.2.1)
- Status: ICE
- Internal compiler error in gimplify_expr at gimplify.cc:20443

### Dev gfortran (gcc-build/gcc/gfortran)
- Status: ICE
- Internal compiler error in gimplify_expr at gimplify.cc:21278

### Intel ifx 2025.2.1
- Status: PASS
- Compiles without errors

## Reproducer

See `reproducer.f90` - constructor interface with finalizer.

## Notes

**THIS IS AN ACTIVE, UNFIXED BUG.** Both system (15.2.1) and dev (16.0) compilers
fail with ICE. This is a priority candidate for investigation and fixing.
