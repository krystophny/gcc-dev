# GCC PR104684 - Coarray ICE in verify_gimple

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=104684
**Status:** RESOLVED FIXED
**Title:** [12/13/14/15 Regression] [coarray] ICE: verify_gimple failed (non-trivial conversion in component_ref)

## Description

This bug triggers an internal compiler error when compiling Fortran code with
coarray features and pointer assignments involving allocatable arrays within
derived types. The compiler crashes during gimple verification rather than
properly handling the pointer assignment.

## Expected Behavior

Pointer components should successfully reference allocatable array components
from other derived types in coarray contexts.

## Actual Behavior

- GCC 12-15: ICE during gimple verification
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

See `reproducer.f90` - coarray test with pointer to allocatable array.
Must compile with `-fcoarray=single`.

## Fix Details

The fix involved modifying `gfc_conv_expr_descriptor` to recognize when only
pointer/allocatable attributes differ between array types, then applying a view
conversion to handle the assignment properly, avoiding the gimple verification error.
