# Test Failure Analysis – finalize_55.f90 (2025-11-20)

## Status
`finalize_55.f90` still fails at all optimization levels. All other targeted finalizer tests currently pass (42, 49, constructor_1, 39, 41, 45).

## Observed Behavior
- Expected finalizer counter: 16 (every elemental result finalized once)
- Actual: counter stops at 14. Missing two finalizations for the elemental result of `elem2(elem(y), elem(y))`.
- GIMPLE for the scalarized assignment shows finalization of the two input elem temporaries (`desc.13`, `desc.14`) but no `_final` call for the result temporary `atmp.11` before it is freed.

## Hypothesis
The scalarized assignment path frees the array temporary produced by the elemental function result without routing it through `__vtab_types_T._final`. The temporary descriptor is available (`atmp.11`), but we never call `gfc_finalize_tree_expr` on it.

## Work Done
- Added finalization hook for array temporaries in `trans-array.cc` (finalize before freeing when type is finalizable).
- Added RHS temporary finalization hook in `trans-expr.cc` for finalizable RHS expressions.
- These hooks were sufficient for finalize_42/49, but `finalize_55` still lacks a `_final` on the result temporary.

## Next Diagnostic Steps
1. In `gfc_trans_scalarized_assignment`, ensure the array temporary descriptor used for elemental results is handed to `gfc_finalize_tree_expr` (not just the data pointer). Confirm via `-fdump-tree-gimple` that `_final` is emitted for `atmp.*` before the free.
2. Re-run `make -k check-gfortran RUNTESTFLAGS="dg.exp=finalize_55.f90"` and the full `finalize_*` subset to verify the counter reaches 16 and no regressions occur.

## Lessons Carried Forward
- Elemental RHS temporaries need explicit finalization; freeing the data pointer alone is insufficient.
- GIMPLE dumps are the quickest way to see whether `_final` is emitted for a temporary; scan for `_final` against the temporary descriptor symbol (e.g., `atmp.*`).
- Guard RHS function-actual finalization to INTENT(OUT/INOUT/VALUE) to avoid over-finalization (fixed finalize_41/42/45/49).
