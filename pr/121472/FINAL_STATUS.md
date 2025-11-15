# PR121472 Finalization Fix - Current Status

## Summary

Full ISO-compliant fix completed for PR121472. Constructor finalization keeps the documented F2008 compatibility behavior, and function results from user-defined assignments are now finalized after the call per F2018 §7.5.6.3.

## Test Results

### ✅ finalize_38a.f90 - PASS
- Passes with `-std=f2008` (backward compatibility mode)
- Emits f08/0011 compatibility warnings as expected
- Constructor finalization toggles off automatically for F2018/F2023/default

### ✅ finalize_45.f90 - PASS
- Function result is finalized after the user-defined assignment
- `final_counts=2`, `assoc_counts=2`, matching Intel ifx/nvfortran

### ✅ finalize_55.f90 - PASS
- Elemental function temporaries are evaluated once and finalized post-call
- Counter reaches 16 as required by ISO/IEC 1539-1:2018 §7.5.6.3

## Changes Committed

### gcc/fortran/resolve.cc
- Added `must_finalize = 1` for function results in user-defined assignments
- Ensures RHS function expressions are marked for finalization

### gcc/fortran/trans-expr.cc
- Restored upstream `gfc_notification_std(GFC_STD_F2018_DEL)` logic
- Fixes constructor finalization with proper standard version handling
- Removed incorrect unconditional constructor finalization disable

## Remaining Work

### Function Result Finalization

- `gfc_conv_procedure_call` now evaluates and finalizes derived function actuals **after** the callee returns when they feed user-defined assignments. This prevents premature cleanup and double finalization of class temporaries.
- Class dummy arguments remain on the existing path so class temporaries retain their descriptor-managed lifecycle.

### Test Suite Validation (2025-11-15)
- Command: `cd gcc-build/gcc && make -j32 -k check-gfortran`
- Result: 3392 expected passes, 0 unexpected failures, 2 unsupported
- Confirms finalize_45/finalize_55 plus the broader regression suite are green before submission.
