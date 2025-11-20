# PR121472 finalize_55 Investigation Summary (2025-11-20)

## Objective
Fix over-finalization in finalize_55.f90 per /tmp/PLAN-gcc.md

## Investigation Findings

### Root Cause
Commit 36fc73d6c14 added finalization code in `gfc_trans_create_temp_array` that was too broad:
- Finalized ALL temporary arrays including descriptor wrappers
- Caused ICEs in finalize_38a.f90: "expected class 'expression', have 'declaration' (var_decl)"
- The code couldn't distinguish between:
  1. Temp arrays holding function results (should finalize)
  2. Descriptor wrappers for passing arrays (should NOT finalize)
  3. Dependency-breaking temps (conditional finalization)

### Commits Made

1. **94511b1d5f0**: Disabled problematic finalization with #if 0
   - Documented ICE issues
   - Identified that both trans-array.cc and trans-expr.cc additions caused problems

2. **647d2477689**: Reverted problematic finalization entirely  
   - Removed finalization code from gfc_trans_create_temp_array
   - Removed finalization code from gfc_trans_assignment_1
   - Kept trans-expr.cc change from 911056b2c91 (fsym != NULL guard)
   - Result: finalize_38a.f90 compiles without ICE

### Test Results After Revert

✅ **finalize_38a.f90**: Compiles cleanly at all optimization levels (ICE fixed)
⚠️  **finalize_55.f90**: Still has over-finalization issue from earlier commits

### Technical Analysis

The GIMPLE dumps revealed:
- finalize_55.f90 test1: Expected ctr=6, got ctr=12 (double finalization)
- Multiple `desc.XX` descriptors being finalized per element
- Both per-element AND array-temp finalization occurring

The finalization needs to happen at exactly ONE of these points:
- Per-element in scalarized loop (for elemental results)
- OR array-temp level (for non-elemental results)
- NOT both

### Recommended Next Steps

1. **Redesign finalization approach**:
   - Add a flag to `gfc_ss_info` to explicitly mark "needs finalization"
   - Set flag only for temps that hold newly-created finalizable objects
   - Check flag in `gfc_trans_create_temp_array` before finalizing

2. **Alternative approach**:
   - Move finalization to where temps are USED, not where they're created
   - Finalize in assignment target handling after value is copied

3. **Guard improvements needed**:
   - Check `ss->info->type == GFC_SS_TEMP` (scalarizer temps only)
   - Verify temp holds function results, not input arrays
   - Avoid finalizing descriptor wrappers created for parameter passing

### Files Modified

- `gcc/fortran/trans-array.cc`: Removed finalization in gfc_trans_create_temp_array
- `gcc/fortran/trans-expr.cc`: Removed finalization in gfc_trans_assignment_1

### Branch Status

Branch: `pr121472-constructor-finalizer-ice`  
Latest commit: 647d2477689
Status: Clean build, finalize_38a ICE resolved, finalize_55 issue remains
