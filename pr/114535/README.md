# GCC PR114535 - ICE with elemental finalizer

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=114535
**Status:** RESOLVED FIXED
**Title:** [13 regression] ICE with elemental finalizer

## Description

This bug triggers an internal compiler error when compiling code with an elemental
finalizer across multiple modules. The problem occurs because gfortran unnecessarily
generated final wrappers for unreferenced symbols, causing the ICE.

## Expected Behavior

Code with elemental finalizers should compile cleanly across module boundaries.

## Actual Behavior

- GCC 13-14: ICE in gfc_trans_call at fortran/trans-stmt.cc:400
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

See `reproducer.f90` - multi-module test with elemental finalizer.

## Fix Details

Fixed by removing code in `resolve.cc` that checked for finalization of unreferenced
symbols. The fix was applied to GCC 13 through 15 branches.
