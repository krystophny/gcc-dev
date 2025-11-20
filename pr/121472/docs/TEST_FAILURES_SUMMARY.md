# Test Suite Failures Summary (2025-11-20)

## Current Status

❌ **1 unexpected test failure**: `finalize_55.f90` (all OPT levels)

- Targeted runs:
  - `finalize_42.f90` ✅ PASS
  - `finalize_49.f90` ✅ PASS
  - `finalize_55.f90` ❌ FAIL (ctr ends at 14, expected 16)

## Failing Test: finalize_55.f90

**Test:** `gfortran.dg/finalize_55.f90`  
**Expected behavior (ISO/IEC 1539-1:2018 §7.5.6.3):** Each elemental function result used in the elemental assignment is finalized exactly once; total finalizer count should reach 16 in the test harness.  
**Actual:** Finalizer count stops at 14 — two finalizations for the elemental `elem2` result array temporary are missing.

### Current Hypothesis
- The scalarized assignment path frees the array temporary produced for the elemental function result without going through `__vtab..._final`, so two elements never get finalized.
- GIMPLE shows finalization of the input element temporaries (`desc.13`, `desc.14`) but **no** finalization call for the result temporary `atmp.11` before it is freed.

### Active Work
- Added hooks to finalize RHS temporaries:
  - `trans-array.cc`: finalize array temps before freeing storage when the temporary’s type is finalizable.
  - `trans-expr.cc`: emit finalization for RHS temporaries when `expr2` is finalizable.
- Despite these hooks, the generated GIMPLE for `finalize_55` still lacks a `_final` call for `atmp.11`; fix is incomplete.

### Next Steps
1. Ensure `gfc_trans_scalarized_assignment` passes the temporary descriptor (not the data pointer) into `gfc_finalize_tree_expr` for elemental-result temps; confirm `_final` call appears ahead of the free in GIMPLE.  
2. Re-run `make -k check-gfortran RUNTESTFLAGS="dg.exp=finalize_55.f90"` and full `finalize_*` sweep.  
3. Once finalizer count reaches 16, rerun broader smoke to guard regressions.

## Fixed Since Last Update
- Double-finalization in `finalize_41/42/45/49` resolved by tightening RHS function-actual finalization and adding guards; tests now pass.
