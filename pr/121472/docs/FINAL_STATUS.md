# PR121472 Finalization Fix - Current Status (2025-11-20)

## Summary
- ICE fixed; core PR reproducer clean.
- Finalization regressions partially addressed: finalize_42/49 (and related) now pass after RHS finalization guards. **finalize_55 remains failing** (missing finalization of elemental result temp).

## Latest Test Snapshot
- Build: `make -j32` ✅
- Targeted tests:
  - `finalize_42.f90` ✅ 12 passes
  - `finalize_49.f90` ✅ 2 passes
  - `finalize_55.f90` ❌ unexpected failures at all OPT levels (counter 14/16)

## Changes in Progress
- `resolve.cc`: mark non-alloc/pointer RHS function results in UDA as `must_finalize`.
- `trans-expr.cc`: guard finalization of RHS function actuals to INTENT OUT/INOUT/VALUE; add RHS temporary finalization hook.
- `trans-array.cc`: finalize array temporaries before freeing when type is finalizable.

## Remaining Work
- Emit `_final` for elemental result temporaries (e.g., `atmp.*` in finalize_55) before freeing their storage.
- Re-run `dg.exp=finalize_*.f90` after fix, then broader smoke.

## ISO Compliance Notes
- Current failure is a non-compliance with ISO/IEC 1539-1:2018 §7.5.6.3: elemental function results must be finalized once; we are skipping two elements in finalize_55.
