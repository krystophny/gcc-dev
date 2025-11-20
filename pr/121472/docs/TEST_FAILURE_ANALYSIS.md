# Test Failure Analysis – finalize_55.f90 (2025-11-20)

## Status
`finalize_55.f90` still fails at all optimization levels. All other targeted finalizer tests currently pass (42, 49, constructor_1, 39, 41, 45).

## Observed Behavior
- Expected finalizer counter: 6 at STOP 2, 16 at STOP 4.
- Actual: counter is already 12 at STOP 2 (over-finalization), then stalls before reaching 16.
- GIMPLE for the scalarized assignment shows *two* per-element `_final` calls (`desc.27` and `desc.29`) plus the array-temp finalization, which explains the over-count.

## Hypothesis
Scalarized assignment is finalizing each elemental result more than once (two descriptor wrappers) and then finalizing the temporary array, producing ctr=12 by STOP 2. We need exactly one finalization per element plus the expected later finalizations.

## Work Done
- Added finalization hook for array temporaries in `trans-array.cc` (finalize before freeing when type is finalizable) and ensured dependency-breaker temps carry the originating expr.
- Added RHS temporary finalization hook in `trans-expr.cc` for finalizable RHS expressions.
- Result: input temps finalize correctly, array temp finalizes, but duplicate per-element finalization remains.

## Next Diagnostic Steps
1. In `gfc_trans_scalarized_assignment`, remove the second per-element `_final` path (desc.29) so each element is finalized exactly once.
2. Confirm via `-fdump-tree-gimple` that only one `_final` per element remains, the array temp finalization still executes, and the counter hits 6 then 16.
3. Re-run `make -k check-gfortran RUNTESTFLAGS="dg.exp=finalize_55.f90"` and the full `finalize_*` subset to verify the counter reaches 16 with no regressions.

## Lessons Carried Forward
- Elemental RHS temporaries need explicit but **single** finalization; avoid multiple descriptor wrappers.
- GIMPLE dumps are the quickest way to see whether `_final` is emitted for a temporary; scan for `_final` against the temporary descriptor symbol and count unique calls.
- Guard RHS function-actual finalization to INTENT(OUT/INOUT/VALUE) to avoid over-finalization (fixed finalize_41/42/45/49).
