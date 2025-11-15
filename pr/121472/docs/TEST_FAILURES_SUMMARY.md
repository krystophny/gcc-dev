# Test Suite Failures Summary

## Current Status (2025-11-15)

❌ **1 unexpected test failure**: finalize_49.f90

- Expected passes: 3391
- Unexpected failures: 1
- Unsupported: 2

## Failing Test: finalize_49.f90

**Test:** `gfortran.dg/finalize_49.f90`
**Expected:** 1 finalization check (`_final != 0B`)
**Actual:** 2 finalization checks
**Status:** REGRESSION introduced by PR121472 finalization changes

### Root Cause Analysis

The test validates F2018 §7.5.6.3 paragraph 6: specification expression function results must be finalized before executable constructs.

Test expression:
```fortran
real tmp(component(finalizable_t(component=1)))
```

This creates nested function calls:
1. `finalizable_t(component=1)` - constructor returns finalizable object
2. `component(...)` - extracts integer from that object for array dimension

**Expected behavior (1 finalization):**
- Function result finalized once after use in specification expression

**Actual behavior (2 finalizations):**
- Our implementation generates TWO finalization checks in tree dump
- Both point to deep-copied objects (desc.10 and desc.11)
- System gfortran (GCC 15.2.1) generates only ONE finalization check

### Technical Details

Tree dump analysis shows:
- Line 294-296: desc.10 created, points to D.4800 (first deep copy)
- Line 311-313: desc.11 created, points to D.4820 (second deep copy)
- Line 320-322: Finalization via desc.10
- Line 324-326: Finalization via desc.11

Both descriptors point to separately malloc'd deep copies of the same original data.

System gfortran generates only desc.10, no desc.11.

### Attempted Fixes (All Failed)

1. Removed deep copy from `else` branch in trans.cc - no change in behavior
2. Removed deep copy from `direct_byref` branch - no change in behavior
3. Removed ALL deep copy calls - no change in behavior

The double finalization is NOT caused by the `gfc_copy_alloc_comp_no_fini` calls.

### Next Steps for Resolution

The root cause is that `gfc_finalize_tree_expr` is being called TWICE for the same expression chain:
1. Once for `finalizable_t()` function result (trans-expr.cc:8835)
2. Once for passing that result to `component()` (trans-expr.cc:8093)

**Possible solutions:**
- Add flag to mark expressions as already-finalized
- Detect when argument expression is already a finalized function result
- Adjust finalization logic to avoid duplicate finalization of nested function calls

**Status:** Needs deeper investigation of expression tree traversal and finalization call sites.

## Previous Status

All previously failing finalization tests (finalize_43/47/51/55/56 and finalize_constructor_1) now pass at every optimization level after guarding duplicate finalizations.
