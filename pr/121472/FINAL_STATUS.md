# PR121472 Finalization Fix - Current Status

## Summary

Partial fix committed for PR121472 finalization issues. Constructor finalization backward compatibility restored, but function result finalization still needs work.

## Test Results

### ✅ finalize_38a.f90 - PASS
- Passes with `-std=f2008` (backward compatibility mode)
- Issues appropriate warnings about f08/0011 corrigendum
- Constructor finalization works correctly with standard flags

### ❌ finalize_45.f90 - FAIL (STOP 3)
- **Issue**: Function result not finalized after user-defined assignment
- **Expected**: 2 finalizations (function result + old LHS from intent(out))
- **Actual**: 1 finalization (only old LHS)
- **Root cause**: `must_finalize` flag set but finalization happens before call, not after

### ❌ finalize_55.f90 - FAIL (STOP 2)
- **Issue**: Elemental function results not fully finalized
- **Status**: Pre-existing issue, may be unrelated to PR121472

## Changes Committed

### gcc/fortran/resolve.cc
- Added `must_finalize = 1` for function results in user-defined assignments
- Ensures RHS function expressions are marked for finalization

### gcc/fortran/trans-expr.cc
- Restored upstream `gfc_notification_std(GFC_STD_F2018_DEL)` logic
- Fixes constructor finalization with proper standard version handling
- Removed incorrect unconditional constructor finalization disable

## Remaining Work

### Function Result Finalization (finalize_45)

**Problem**: In `gfc_trans_call`, argument finalization code is added to `se.finalblock` which gets merged into `se.pre` (before the call). For user-defined assignments, we need finalization AFTER the call.

**Solution Path**:
1. Modify `gfc_conv_procedure_call` to detect user-defined assignment context
2. For function result arguments with `must_finalize=1`, defer finalization
3. Add deferred finalization to `se.post` instead of `se.pre`
4. Ensure finalization happens after assignment subroutine returns

**Key Code Locations**:
- `trans-stmt.cc:518-519` - where finalblock is added to pre
- `trans-expr.cc:gfc_conv_procedure_call` - argument evaluation
- Need to pass `dependency_check` flag or detect assignment context

## Next Steps

1. Implement deferred finalization for user-defined assignment arguments
2. Run full gfortran test suite
3. Fix any regressions
4. Verify 100% pass rate before final submission
