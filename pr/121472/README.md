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
- Status: ICE (before fix)
- Internal compiler error in gimplify_expr at gimplify.cc:20443

### Dev gfortran (gcc-build/gcc/gfortran with PR121472 ISO-compliant fix)
- Status: PASS
- Compiles cleanly
- Runtime output: `constructor: 1`, `finalizer: 2`
- ✅ **STANDARD-COMPLIANT**: Correct Fortran 2018 behavior
- Finalizes function result after assignment + variable at scope exit

#### Full testsuite validation (2025-11-15)
- Command: `make -j32 -k check-gfortran` from `gcc-build/gcc`
- Result: 3392 expected passes, 0 unexpected failures, 2 unsupported
- All finalization regressions (`finalize_{43,45,47,51,55,56}` and `finalize_constructor_1.f90`) now PASS across optimization levels.

### Intel ifx 2025.2.1
- Status: PASS
- Compiles cleanly
- Runtime output: `constructor: 1`, `finalizer: 2`
- Standard-compliant: finalizes function result + variable at scope exit

### NVIDIA nvfortran 25.9
- Status: PASS
- Compiles cleanly
- Runtime output: `constructor: 1`, `finalizer: 2`
- Standard-compliant: finalizes function result + variable at scope exit

### LLVM Flang (flang-new 21.1.5)
- Status: PASS
- Compiles with warning about undefined function result (benign)
- Runtime: no output (no finalization printed)
- No ICE, clean compilation

### LFortran
- Status: PASS
- Compiles cleanly with no warnings
- Runtime: no output (no finalization printed)
- No ICE, clean compilation

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
