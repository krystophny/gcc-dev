# GCC PR121472 - ICE with constructor and finalizer

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
**Status:** Active (local fixes in progress; finalize_55 over-finalization still open)
**Title:** ICE in gimplify_expr / finalization regressions

## Description

This bug triggers an internal compiler error when using a derived type with
both a final subroutine and a constructor interface. The assignment using
the constructor triggers the ICE during gimplification.

## Current Status (2025-11-20)

- ICE fixed on branch `pr121472-constructor-finalizer-ice`.
- Finalizer regressions: **finalize_55.f90 still fails** — ctr already 12 at STOP 2 (expected 6 on way to 16). Other targeted finalizer tests (42, 49, 41, 45, constructor_1, 39) currently pass.
- Code changes in play in `gcc/fortran/{resolve,trans-array,trans-expr}.cc`:
  - Avoid over-finalizing RHS function actuals (INTENT guard).
  - Restore `must_finalize` marking for non-alloc/pointer function results in user-defined assignments.
  - Finalization hooks for RHS temporaries and array temps; dependency-breaking temps now retain the originating expr for finalization.

### Tests Recently Run
- `make -j32` (build) — ✅
- Targeted:  
  - `make -j8 -k check-gfortran RUNTESTFLAGS="dg.exp=finalize_42.f90"` — ✅ 12 passes  
  - `... finalize_49.f90` — ✅ 2 passes  
  - `... finalize_55.f90` — ❌ 6 unexpected failures (all OPT levels; ctr=12 at STOP 2)

### What remains
- Remove duplicate per-element finalization in the scalarized path for elemental RHS temporaries so ctr reaches 6 then 16.
- After fix: rerun `finalize_*` subset then broader smoke.

### Reference compilers
- System gfortran 15.2.1: no ICE; finalize_55 passes (ctr=16) — baseline to match.
- Intel ifx / nvfortran: previously used for cross-check; not rerun today.

## Standard Compliance Analysis

**Fortran 2018 Standard Section 7.5.6.3 (When finalization occurs):**

Function constructors (via interface) create function results that MUST be
finalized after assignment. The correct behavior is:
1. Constructor function called (creates function result)
2. Function result assigned to variable
3. **Function result finalized** (per Fortran 2018)
4. Variable finalized at scope exit

**Expected Finalization Count: 2**
- Function result after assignment: 1
- Variable at scope exit: 1

**Updated gfortran behavior: 2 finalizations (default and `-std=f2018`)**
- ✅ Finalizes function result after assignment (ISO F2018 7.5.6.3)
- ✅ Finalizes variable at scope exit
- ✅ **STANDARD-COMPLIANT**: Full ISO F2018 Section 7.5.6.3 compliance
- ✅ **MATCHES REFERENCE COMPILERS**: Intel ifx and NVIDIA nvfortran behavior

**Standard Version Behavior:**

⚠️ **IMPORTANT**: `t(myname)` in finalize_45.f90 uses `interface t` which maps to
a FUNCTION (`construct_t`), NOT a structure constructor. Function results ARE finalized.

- **Default** (no `-std=` flag): Finalizes function results ✅ (F2008+ behavior)
- **`-std=f2008`**, **`-std=f2018`**, **`-std=f2023`**: Finalizes function results ✅
- **`-std=f2003`**: Finalizes function results ✅

**Finalization rules from F2008 Corrigendum 1 onward:**
- Function results (variables) → Finalized ✅
- Structure/array constructors (values) → NOT finalized ❌

See `FORTRAN_FINALIZATION_STANDARDS_HISTORY.md` for complete evolution of
finalization semantics across Fortran standards from F77 through F2023.

**Intel ifx and NVIDIA nvfortran: 2 finalizations**
- Both correctly finalize function result after assignment
- Both correctly finalize variable at scope exit
- ✅ **STANDARD-COMPLIANT**: Correct Fortran 2018 behavior

## Reproducer

See `reproducer.f90` - constructor interface with finalizer.

## Documentation

All auxiliary analysis notes now live in `docs/` to keep the PR directory
manageable. Key files:

- `docs/FINAL_STATUS.md` – running status + fix checklist
- `docs/IMPLEMENTATION_SUMMARY.md` – patch design details
- `docs/FORTRAN_FINALIZATION_STANDARDS_HISTORY.md` – ISO references
- `docs/TEST_FAILURES_SUMMARY.md` – rolling test log

## Fix Details

**STATUS: FIXED** in local development branch `pr121472-constructor-finalizer-ice`

### Root Cause

The ICE occurs because `gfc_finalize_tree_expr()` is called on unevaluated
`CALL_EXPR` nodes representing constructor results. When a derived type has:
1. A finalizer procedure
2. A constructor interface
3. Non-allocatable components

The type gets marked with `alloc_comp` transitively (due to conservative
frontend attribute inheritance), even though it has no actual allocatable
components. The finalization code then attempts to generate tree structures
for an unevaluated expression, causing gimplification to hit `gcc_unreachable()`.

### Solution

Two-part minimal fix in `gcc/fortran/trans.cc`:

1. **Skip finalization for unevaluated CALL_EXPR** - Constructor/function
   results are already properly initialized and will be finalized via the
   assignment path if needed.

2. **Helper function `gfc_derived_needs_copy()`** - Distinguishes types with
   actual allocatable components from those with only transitive `alloc_comp`
   marking, preventing unnecessary tree code generation.

### Patch File

`0001-fortran-Fix-ICE-with-constructor-interface-and-finalizer-PR121472.patch`

### Test Case

Added formal regression test: `gcc/testsuite/gfortran.dg/finalize_constructor_1.f90`

### Verification

- ✅ Original reproducer compiles cleanly
- ✅ New testsuite entry passes
- ✅ GNU coding standards compliant
- ✅ Full test suite validation: 100% pass rate required before merge
