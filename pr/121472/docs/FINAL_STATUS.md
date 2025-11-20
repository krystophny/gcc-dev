# PR121472 Finalization Fix - Current Status (2025-11-20)

## Summary
- ICE fixed; core PR reproducer still clean.
- Finalization regressions partially addressed: finalize_42/49 (and related) pass after RHS finalization guards. **finalize_55 now fails due to over‑finalization (ctr = 12 at first checkpoint, expected 6/16).**

## Latest Test Snapshot
- Build: `make -j32` ✅
- Targeted tests:
  - `finalize_42.f90` ✅ 12 passes
  - `finalize_49.f90` ✅ 2 passes
  - `finalize_55.f90` ❌ unexpected failures at all OPT levels (counter reaches 12 by the first STOP; should be 6 then 16 total)

## Changes in Progress
- `resolve.cc`: mark non-alloc/pointer RHS function results in UDA as `must_finalize`.
- `trans-expr.cc`: guard finalization of RHS function actuals to INTENT OUT/INOUT/VALUE; add RHS temporary finalization hook.
- `trans-array.cc`: finalize array temporaries before freeing when type is finalizable; temporary SS for dependency-breaking now remembers the originating expr to drive finalization.

## Remaining Work
- Stop double-finalizing elemental temporaries in the scalarized path: GIMPLE shows two `_final` calls per element (`desc.27` and `desc.29`) plus array-temp finalization, producing ctr=12 at STOP 2.
- Re‑run `dg.exp=finalize_*.f90` after the fix, then broader smoke.

## ISO Compliance Notes
- Current failure is a non‑compliance with ISO/IEC 1539-1:2018 §7.5.6.3: elemental function results must be finalized exactly once. We are finalizing too many elements (over‑finalization to 12 by mid-test) and still not reaching the expected total.
