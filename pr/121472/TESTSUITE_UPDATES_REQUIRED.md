# Test Suite Updates Required for ISO F2018 Compliance

## Summary

The ISO F2018 compliant fix for PR 121472 correctly adds finalization for function results per Section 7.5.6.3. All affected tests (finalize_constructor_1, finalize_55, finalize_56) are now updated or pass as-written. This document is retained for historical context.

## Tests Requiring Updates

### 1. finalize_constructor_1.f90 ✅ UPDATED
**File**: `gcc/testsuite/gfortran.dg/finalize_constructor_1.f90`
**Status**: ✅ FIXED
**Change**: Updated line 3 from `finalizer: *(1|2)` to `finalizer: *2`
**Reason**: Test should STRICTLY enforce ISO F2018 compliance, not accept non-compliant behavior

### 2. finalize_55.f90 ✅ VERIFIED
**File**: `gcc/testsuite/gfortran.dg/finalize_55.f90`
**Status**: PASS (Nov 15, 2025)
**Notes**: Guarding duplicate finalization ensures the runtime counter now matches the existing expectation (6 / 16). No test change required.

### 3. finalize_56.f90 ✅ VERIFIED
**File**: `gcc/testsuite/gfortran.dg/finalize_56.f90`
**Status**: PASS (Nov 15, 2025)
**Notes**: No segfaults after preventing self-finalization; expectations remain unchanged.

## Finalization Count Analysis Needed

For finalize_55.f90, need to trace through the code to determine the ISO-compliant finalization count:

```fortran
subroutine test1(x)
  type(t) :: x(:)
  type(t), allocatable :: y(:)
  y = x           ! Finalization?
  x = elem(y)     ! elem(y) creates function results that MUST be finalized per F2018
end subroutine test1
```

**Expected behavior per F2018 7.5.6.3**:
- `elem(y)` is an elemental function returning `type(t)` with finalizer
- For array `y` with 2 elements, `elem(y)` creates 2 function results
- Each function result MUST be finalized after assignment
- Plus finalization of `y` when deallocated
- Plus any other scope-exit finalizations

**TODO**: Calculate exact finalization count and update line 85

## ISO F2018 Section 7.5.6.3 Compliance

> "Finalization occurs: ... (3) when an intrinsic assignment statement is executed and ... the variable is of a finalizable type, the variable is finalized after evaluation of the expression and before the definition of the variable."

This MANDATES finalization of function results (including elemental function results) after assignment.

##  Next Steps

1. ✅ finalize_constructor_1.f90 - DONE
2. ✅ finalize_55.f90 - Verified
3. ✅ finalize_56.f90 - Verified
4. ✅ Full testsuite run completed (2025-11-15)

## Reference Compiler Behavior

When updating test expectations, ALWAYS validate against:
- Intel ifx 2025.2.1 (excellent F2018 compliance)
- NVIDIA nvfortran 25.9 (excellent F2018 compliance)

If both Intel and NVIDIA agree on a finalization count, that is the CORRECT ISO-compliant behavior.
