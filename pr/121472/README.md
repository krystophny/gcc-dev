# GCC PR121472 - ICE with constructor and finalizer

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
**Status:** Active (ICE fixed, temp metadata infrastructure in place, finalize_55 over-finalization remains)
**Branch:** `pr121472-finalizer-clean`
**Title:** ICE in gimplify_expr / finalization regressions

## Current Status (2025-11-20)

### Fixed
- ✅ ICE fixed: Original reproducer compiles cleanly
- ✅ Deep copy guard prevents self-referencing ICE in assignment helpers
- ✅ Temp metadata infrastructure added (typespec, rank, finalizable tracking)

### In Progress
- ⚠️ **finalize_55.f90 over-finalization**: counter = 12 at first checkpoint (expected 6→16)
- Need to implement finalization consumer logic that uses temp metadata
- Need temp teardown finalization using `temp_finalizable` flag

### ISO Compliance Status
❌ **NON-COMPLIANT** with ISO/IEC 1539-1:2018 Section 7.5.6.3
- Over-finalization: elemental function results finalized multiple times
- Expected: exactly one finalization per function result
- Actual: multiple finalization calls per element (per-element + array-temp)

### Latest Test Results
- Build: `make -j32` ✅
- finalize_42.f90: ✅ 12 passes
- finalize_49.f90: ✅ 2 passes
- finalize_55.f90: ❌ unexpected failures (counter=12, expected 6→16)

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

**Remaining Work:**
- ❌ Implement finalization consumer that reads temp_finalizable
- ❌ Add finalization at temp teardown using stored metadata
- ❌ Fix finalize_55 over-finalization bug

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

**Current GCC behavior (NON-COMPLIANT):**
- Multiple finalization calls per element
- Per-element finalization in scalarized loop
- Array-temp finalization
- Descriptor finalization
- Result: counter = 12 instead of expected 6

**Reference compiler behavior (COMPLIANT):**
- Intel ifx: correct count (16 total in finalize_55)
- NVIDIA nvfortran: correct count (16 total)
- System gfortran 15.2.1: correct count (16 total)

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

## Next Steps

1. **Implement temp finalization consumer**:
   - Find temp teardown location in gfc_trans_create_temp_array
   - Check ss_info->temp_finalizable
   - Call finalization for temp using ss_info->temp_ts metadata

2. **Fix finalize_55 over-finalization**:
   - Ensure one-time finalization per temp (not per-element)
   - Verify with GIMPLE dumps
   - Test counter reaches 6, then 16 (not 12)

3. **Verify ISO compliance**:
   - Test against reference compilers
   - Verify finalization count matches standard
   - Document compliance in commit message

4. **Clean commit for upstream**:
   - Ensure 100% test pass rate
   - Update commit message with ISO references
   - Run full test suite
   - Export patch when ready
