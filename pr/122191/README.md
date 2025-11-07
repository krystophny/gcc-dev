# GCC PR122191 - ICE with composite PDT result

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122191
**Status:** RESOLVED FIXED
**Title:** ICE on function interface body with composite PDT result

## Description

This bug triggers an internal compiler error when processing parameterized
derived types (PDTs) with interface bodies and allocatable array components.
The compiler crashes during gimplification when three conditions are met:
exactly two derived types, an interface body declaration, and an allocatable
array component.

## Expected Behavior

PDTs with interface bodies and allocatable components should compile cleanly.

## Actual Behavior

- Older GCC: ICE in gimplify_var_or_parm_decl at gimplify.cc:3354
- Modern GCC: Fixed

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

See `reproducer.f90` - PDT interface body with allocatable array.

## Fix Details

Fixed on October 13, 2025, by Paul Thomas. The fix checks for parameterized
components before attempting deallocation, preventing the ICE during compilation.
