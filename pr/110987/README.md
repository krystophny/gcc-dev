# GCC PR110987 - Segfault with finalization of temporary

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110987
**Status:** RESOLVED FIXED
**Title:** [13 Regression] Segmentation fault after finalization of a temporary variable

## Description

This bug causes a segmentation fault when finalizing temporary variables in
inheritance scenarios where a derived type inherits from a parent but has no
data members of its own. The crash occurs when the compiler incorrectly
finalizes temporary variables, deallocating memory still in use.

## Expected Behavior

Code should compile and execute without segmentation faults. Temporaries should
be correctly tracked and finalized only when truly out of scope.

## Actual Behavior

- GCC 13.2.0: Segmentation fault at runtime
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

See `reproducer.f90` - inheritance test with zero-component derived type and finalizers.

## Fix Details

The fix involved correcting how the compiler determines whether a type has components,
checking directly rather than relying on a zero-components attribute, and treating
elemental zero-component expressions consistently with scalars.
