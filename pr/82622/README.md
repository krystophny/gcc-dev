# GCC PR82622 - ICE with PDT allocation

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82622
**Status:** RESOLVED FIXED
**Title:** [PDT] ICE in structure_alloc_comps, at fortran/trans-array.c:8963

## Description

This bug triggers an internal compiler error when allocating parameterized
derived types (PDTs) with nested type parameters. The compiler crashes with
a segmentation fault during the structure allocation components phase when
attempting to compare parameter names without null pointer validation.

## Expected Behavior

PDTs with nested parameters should allocate cleanly without compiler crashes.

## Actual Behavior

- Older GCC versions: ICE in structure_alloc_comps at fortran/trans-array.c:8963
- Modern GCC: Fixed

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

See `reproducer.f90` - PDT allocation with nested type parameters.

## Fix Details

Paul Thomas fixed this through multiple commits addressing related PDT issues,
including validation checks for null parameter names before string comparison operations.
