# GCC PR121472 - ICE with constructor and finalizer

**Bug URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
**Status:** UNCONFIRMED
**Title:** ICE in gimplify_expr

## Description

This bug triggers an internal compiler error when using a derived type with
both a final subroutine and a constructor interface. The assignment using
the constructor triggers the ICE during gimplification.

## Expected Behavior

Code using constructors and finalizers together should compile cleanly.

## Actual Behavior

- GCC 15.2.1: ICE in gimplify_expr at gimplify.cc:20443
- GCC 16.0 dev: ICE in gimplify_expr at gimplify.cc:21278
- Status: ACTIVE BUG - reproducible on current versions

## Test Results

### System gfortran (GNU Fortran 15.2.1)
- Status: ICE
- Internal compiler error in gimplify_expr at gimplify.cc:20443

### Dev gfortran (gcc-build/gcc/gfortran)
- Status: ICE
- Internal compiler error in gimplify_expr at gimplify.cc:21278

### Intel ifx 2025.2.1
- Status: PASS
- Compiles without errors

## Reproducer

See `reproducer.f90` - constructor interface with finalizer.

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
- ✅ Independent review by Patrick-Auditor: CONDITIONAL_APPROVE (7/10 cleanliness)
- ✅ Ready for upstream submission
