# Test Suite Failures Summary (2025-11-20)

## Current Status

❌ **1 unexpected test failure**: `finalize_55.f90` (all OPT levels)

- Targeted runs:
  - `finalize_42.f90` ✅ PASS
  - `finalize_49.f90` ✅ PASS
  - `finalize_55.f90` ❌ FAIL (ctr hits 12 at first STOP, expected 6 then 16 total)

## Failing Test: finalize_55.f90

**Test:** `gfortran.dg/finalize_55.f90`  
**Expected behavior (ISO/IEC 1539-1:2018 §7.5.6.3):** Each elemental function result used in the elemental assignment is finalized exactly once; total finalizer count should reach 16 in the test harness.  
**Actual:** Counter reaches 12 at STOP 2 (should be 6 there, then 16 at the end) — we are double-finalizing some elements and still not reaching the final total.

### Current Hypothesis
- Scalarized assignment now finalizes more than once per element: GIMPLE shows two `_final` calls per element (`desc.27` and `desc.29`) plus the array-temp finalization, leading to over-count.
- Even with the extra calls, the total still stops at 12; the final array-level total never reaches 16, suggesting ordering/cleanup still off.

### Active Work
- Added hooks to finalize RHS temporaries:
  - `trans-array.cc`: finalize array temps before freeing storage when the temporary’s type is finalizable.
  - `trans-expr.cc`: emit finalization for RHS temporaries when `expr2` is finalizable.
- After adding `info->expr` to dependency-breaker temps, array temps get finalized, but per-element paths now over-finalize; need to remove the duplicate per-element finalizer call.

### Next Steps
1. In the scalarized assignment path, suppress the second per-element finalization (`desc.29`) so each element is finalized exactly once.  
2. Re-run `make -k check-gfortran RUNTESTFLAGS="dg.exp=finalize_55.f90"` and the full `finalize_*` subset.  
3. Once counts match (6 then 16), rerun broader smoke to guard regressions.

## Fixed Since Last Update
- Double-finalization in `finalize_41/42/45/49` resolved by tightening RHS function-actual finalization and adding guards; tests now pass.
