# GCC PR116669 - Crash on circular derived type

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=116669
**Status:** RESOLVED FIXED
**Title:** compiler crash on circular derived type component definition

## Description

The gfortran compiler crashes with a segmentation fault when processing circular
derived type definitions where types reference each other indirectly through
allocatable components. The code creates a cycle causing gfortran to enter
endless recursion during compilation.

## Expected Behavior

Indirect circular dependencies in derived types should be detected and handled
without compiler crashes. Intel Fortran handles this code correctly.

## Actual Behavior

- GCC 10-14.2.0: Segmentation fault
- GCC 15+: Fixed

## Test Results

### System gfortran (GNU Fortran 15.2.1)
- Status: PASS
- Compiles without errors

### Dev gfortran (gcc-build/gcc/gfortran)
- Status: PASS
- Compiles without errors

### Intel ifx
- Status: SKIP (not installed)

## Reproducer

See `reproducer.f90` - circular type definition with allocatable components.

## Fix Details

Fixed on January 7, 2025, with a patch extending cyclic type detection to properly
identify and handle non-immediate circular dependencies in derived types.
