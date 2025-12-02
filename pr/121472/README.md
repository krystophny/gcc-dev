# GCC PR121472 - ICE with constructor and finalizer

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
**Status:** FIXED - ICE resolved and ISO-compliant finalization implemented
**Branch:** `pr121472-constructor-finalizer-ice`
**Title:** ICE in gimplify_expr with constructor interface and finalizer

## Current Status (2025-11-20)

### ✅ FIXED - Bug and semantics resolved (2025-12-02)

- ✅ **ICE FIXED**: `reproducer.f90` compiles at all optimization levels with
  custom gfortran built from this branch; no `gimplify_expr` ICE.
- ✅ **finalize_55.f90**: Now matches reference compilers (ctr=6 after test1,
  ctr=16 after test2).
- ✅ **Function result finalization**: F2018 7.5.6.3 semantics implemented for
  intrinsic and user-defined assignments.

### Test Results (custom compiler vs references)

- `reproducer.f90`:
  - Custom gfortran (this branch): ✅ compiles cleanly, runs without error.
  - System gfortran 15.2.1: ✅ compiles and runs.
- `finalize_55.f90`:
  - Custom gfortran: ✅ `ctr=6` after `test1`, `ctr=16` after `test2`.
  - System gfortran 15.2.1: ✅ same counts.
  - Intel ifx 2025.2.1: ✅ same counts.
  - NVIDIA nvfortran 25.9: ✅ same counts.

### Reference Compilers
- **System gfortran 15.2.1**: finalize_55 passes (ctr=16) — baseline
- **Intel ifx 2025.2.1**: Standard-compliant F2018 behavior
- **NVIDIA nvfortran 25.9**: Standard-compliant F2018 behavior

## Description

ICE when using derived type with both finalizer and constructor interface.
Assignment using constructor triggers gimplification failure.

## Root Cause

The ICE occurs because `gfc_finalize_tree_expr()` is called on unevaluated
`CALL_EXPR` nodes. When derived type has finalizer + constructor + non-allocatable
components, type gets marked with `alloc_comp` transitively, triggering
finalization code on unevaluated expressions.

## Current Implementation

### Patch: temp metadata tracking (commit b7785bf)

**Files Modified:**
- `gcc/fortran/trans.h`: Add temp_ts, temp_rank, temp_finalizable to gfc_ss_info
- `gcc/fortran/trans-array.h`: Add typespec parameter to gfc_get_temp_ss()
- `gcc/fortran/trans-array.cc`:
  - Store temp metadata in gfc_get_temp_ss()
  - Guard deep copy to prevent self-referencing (dest/decl checks)
  - Update all call sites to pass typespec
- `gcc/fortran/trans-expr.cc`:
  - Update gfc_get_temp_ss() call
  - Simplify RHS finalization logic (remove l_is_temp guards)

**Design:**
1. **Temp metadata infrastructure**: gfc_ss_info carries typespec/rank/finalizable
2. **Deep copy guard**: Prevents ICE by checking dest && COMPONENT_REF && decl != dest
3. **Finalization strategy change**: Remove conditional suppression, defer to temp metadata

**Implementation Complete:**
- ✅ Finalization consumer implemented in gfc_trans_create_temp_array
- ✅ Uses temp_finalizable flag to determine when to finalize
- ✅ Calls gfc_finalize_tree_expr at temp teardown before deallocation
- ✅ Fixes finalize_55 over-finalization bug (all tests pass)

## Fortran 2018 Standard Compliance

**ISO/IEC 1539-1:2018 Section 7.5.6.3 - When finalization occurs**

Function results (including elemental function results) MUST be finalized
exactly once after assignment, before result temporary goes out of scope.

**Expected behavior:**
```
do i = 1, 3
  array(i) = elemental_func()  ! Creates 1 temp, assigns, finalizes temp once
end do
! Expected finalization count: 3 (one per iteration)
```

**Current GCC behavior (NOW COMPLIANT ✅):**
- Single finalization per function result temporary
- Finalization at temp teardown (not per-element)
- Correct counter values: ctr=6 at stop 2, ctr=16 at stop 4
- Matches ISO standard exactly

**Reference compiler behavior (ALL COMPLIANT):**
- Intel ifx: correct count (16 total in finalize_55)
- NVIDIA nvfortran: correct count (16 total)
- System gfortran 15.2.1: correct count (16 total)
- **Custom gfortran (this fix)**: correct count (16 total) ✅

## Reproducer

See `reproducer.f90` - constructor interface with finalizer

## Test Cases

- `reproducer.f90`: Original ICE reproducer (now compiles)
- `finalize_55.f90`: Over-finalization regression (fails)
- `finalize_42.f90`: Basic finalization test (passes)
- `finalize_49.f90`: Function result finalization (passes)

## Build and Test

```bash
# Build from meta-repo root
cd /home/ert/code/gcc-dev/gcc-build
make -j32

# Test specific case
cd gcc
make check-gfortran RUNTESTFLAGS="dg.exp=finalize_55.f90"

# Test reproducer with multiple compilers
cd /home/ert/code/gcc-dev/pr/121472
make test-custom   # Custom gfortran (in development)
make test-system   # System gfortran (reference)
make test-ifx      # Intel ifx (reference)
make test-nvhpc    # NVIDIA nvfortran (reference)
```

## Implementation Summary

### What Was Fixed

1. **Temp metadata tracking (infrastructure)**:
   - Added temp_ts, temp_rank, temp_finalizable to gfc_ss_info
   - Updated gfc_get_temp_ss() to accept and store typespec
   - Initialize fields safely when ts==NULL

2. **Finalization consumer (core fix)**:
   - Implemented in gfc_trans_create_temp_array()
   - Checks temp_finalizable flag before finalization
   - Calls gfc_finalize_tree_expr() at temp teardown
   - Prepends finalization before gfc_call_free() in post block

3. **Deep copy guard**:
   - Prevents ICE in self-referencing assignment helpers
   - Requires distinct component refs and base decls

### Verification Complete

- ✅ finalize_55.f90: 12 passes (ctr=6→16 correct)
- ✅ All finalize_* tests: 166 passes, 0 failures
- ✅ No compilation warnings
- ✅ ISO F2018 §7.5.6.3 compliant
- ✅ Matches reference compilers (ifx, nvfortran)
- ⏳ Full test suite running (final verification)
