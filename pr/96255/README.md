# PR96255: Fortran DO CONCURRENT Type-Spec Implementation

**Status:** Complete - All tests passing (0 unexpected failures)

**Commits:**
- d11074121b3 - Jerry DeLisle's base implementation
- b06716ac489 - Shadow variable walker and resolution fixes

---

## Overview

This PR implements support for the optional Fortran 2008 integer type specification in DO CONCURRENT and FORALL headers:

```fortran
do concurrent (integer(kind=4) :: i = 1:10)
  result(i) = real(i) * 2.0
end do
```

The implementation is split between two patches:

1. **Base Implementation (0001)**: Parsing, shadow variable creation, data structures
2. **Shadow Variable Walker (0002)**: Expression walker, constraint enforcement, bug fixes

---

## Part 1: Base Implementation (d11074121b3)

### Parser Changes (match.cc)

Added type-spec parsing to `match_forall_header()`:
- Detects optional `integer :: ` prefix in DO CONCURRENT/FORALL headers
- Enforces F2008 requirement: type-spec must be INTEGER
- Creates shadow variables when type differs from outer scope

### Shadow Variable Mechanism

When type-spec differs from outer scope variable:
- Creates new symbol with `_` prefix (e.g., `_i` for iterator `i`)
- Sets `iter->shadow = true` flag
- Converts iterator bounds to specified type

Purpose: Avoids type conflicts when DO CONCURRENT type-spec differs from outer scope variable kind.

### Data Structure Changes (gfortran.h)

```c
typedef struct gfc_forall_iterator
{
  gfc_expr *var, *start, *end, *stride;
  gfc_loop_annot annot;
  bool shadow;  /* index-name shadows a variable from outer scope */
  struct gfc_forall_iterator *next;
}
gfc_forall_iterator;
```

---

## Part 2: Shadow Variable Walker and Resolution Fixes (b06716ac489)

### Main Implementation: Shadow Variable Walker

**Purpose:** Completes Jerry's type-spec implementation by substituting references to outer scope variables with their shadow counterparts.

**Implementation (resolve.cc):**
- `replace_in_expr_recursive()`: Recursively walks expressions (variables, array subscripts, substrings, operations)
- `replace_in_code_recursive()`: Recursively walks code blocks (assignments, conditionals, loops)
- `gfc_replace_forall_variable()`: Entry point that replaces all references to a given symbol

**What it does:**
When a DO CONCURRENT has a type-spec that creates shadow variables (with `_` prefix), this walker visits every expression in the loop body and replaces references to the original iterator name with references to the shadow variable. This ensures the loop uses the correct type throughout.

**Example:**
```fortran
integer :: i
do concurrent (integer(kind=8) :: i = 1:10)  ! Creates shadow _i
  print *, i  ! Walker changes this to reference _i, not outer i
end do
```

### Fix 1: Constraint Enforcement (Flag Management)

**Problem:** `gfc_do_concurrent_flag` was never set, breaking F2008 constraint checking (C1139: only PURE procedures allowed in DO CONCURRENT).

**Solution (resolve.cc:13957-13964):**
```c
if (code->op == EXEC_DO_CONCURRENT)
  gfc_do_concurrent_flag = 1;
gfc_resolve_forall (code, ns, forall_save);
if (code->op == EXEC_DO_CONCURRENT)
  gfc_do_concurrent_flag = 2;
```

**Flag states:**
- 0 = Outside DO CONCURRENT
- 1 = Inside DO CONCURRENT body (only PURE procedures allowed)
- 2 = Inside DO CONCURRENT mask (impure functions like SUM allowed)

### Fix 2: NULL Pointer Safety

**Problem:** Shadow variable code could crash on NULL pointers.

**Solution (resolve.cc:12625-12626):**
```c
if (fa->var && fa->var->symtree && var_expr[i] && var_expr[i]->symtree
    && fa->var->symtree->n.sym == var_expr[i]->symtree->n.sym)
```

### Fix 3: Memory Leak Prevention

**Problem:** `var_expr` array allocated twice in nested constructs.

**Solution (resolve.cc:12597):**
```c
if (forall_save == 0 && nvar == 0)
  var_expr = XCNEWVEC (gfc_expr *, total_var);
```

### Fix 4: Iterator Counting

**Problem:** Code only counted FORALL iterators, not DO CONCURRENT.

**Solution (resolve.cc:12394, 12407):**
```c
gcc_assert (code->op == EXEC_FORALL || code->op == EXEC_DO_CONCURRENT);
if (code->op == EXEC_FORALL || code->op == EXEC_DO_CONCURRENT)
  n++;
```

### Fix 5: Obsolescence Warning

**Problem:** Warning fired for both FORALL and DO CONCURRENT.

**Solution (resolve.cc:12588-12590):**
```c
if (code->op == EXEC_FORALL
    && !gfc_notify_std (GFC_STD_F2018_OBS, "FORALL construct at %L", ...))
```

FORALL was marked obsolescent in F2018; DO CONCURRENT is not obsolescent.

### Fix 6: Reduction Warning Suppression

**Problem:** Warning fired for valid reduction-like code in DO CONCURRENT.

**Solution (resolve.cc:12272-12276):**
```c
/* DO NOT emit this warning for DO CONCURRENT - reduction-like
   many-to-one assignments are semantically valid (formalized with
   the REDUCE locality-spec in Fortran 2023).  */
if (!find_forall_index (code->expr1, forall_index, 0)
    && !gfc_do_concurrent_flag)
  gfc_warning (...);
```

**Justification:**

DO CONCURRENT and FORALL have different semantics:
- **FORALL**: Strict iteration independence required
- **DO CONCURRENT**: "Arbitrary order execution" (more permissive)

All major compilers (Intel ifx, NVIDIA nvfortran, HPE cce) have always allowed reductions in DO CONCURRENT. Fortran 2023's REDUCE locality-spec formalizes this existing practice rather than introducing new semantics.

### Code Quality Improvements (match.cc)

**Improvement 1: Enhanced Error Diagnostics**

Replaced generic error messages with descriptive diagnostics:
```c
gfc_internal_error ("Failed to create shadow variable symtree for "
                    "DO CONCURRENT type-spec at %L", &loc);
```

**Improvement 2: Eliminated Code Duplication**

Created `apply_typespec_to_iterator()` helper function to consolidate shadow variable creation logic, removing approximately 70 lines of duplicated code.

---

## Test Results

### Full GCC Fortran Test Suite

```
# of expected passes            74,325
# of expected failures             343
# of unsupported tests              81
# of unexpected failures             0
```

### DO CONCURRENT Tests

All 21 `do_concurrent_*.f90` tests pass, including constraint checking, nested loops, and array operations.

### Multi-Compiler Validation

Tested with:
- Custom gfortran (this build)
- System gfortran (GCC 15.2.1)
- LLVM Flang (21.1.5)
- Intel ifx (2025.2.1)
- NVIDIA nvfortran (25.9-0)

All compilers accept DO CONCURRENT reductions consistently.

---

## Building and Testing

### Build
```bash
cd /home/ert/code/gcc-dev/gcc-build
make -j32
```

### Test Suite

**CRITICAL:** Must run from `gcc-build/gcc/` directory:

```bash
cd /home/ert/code/gcc-dev/gcc-build/gcc
make -j32 -k check-gfortran > /tmp/test.log 2>&1 &
```

Incorrect locations:
- `/home/ert/code/gcc-dev/` (no target)
- `/home/ert/code/gcc-dev/gcc-build/` (no target)
- `/home/ert/code/gcc-dev/gcc/` (source tree)

### Results
```bash
grep "# of" /home/ert/code/gcc-dev/gcc-build/gcc/testsuite/gfortran/gfortran.sum
```

---

## Fortran Standards Compliance

### F2008 Features
- DO CONCURRENT type-spec syntax (R1125)
- Constraint checking (C1139: only PURE procedures allowed)
- Integer type requirement
- Shadow variable creation

### F2018 Features
- FORALL obsolescence warning
- Proper distinction from DO CONCURRENT

### F2023 Considerations
- REDUCE locality-spec acknowledged in comments
- Reduction semantics correctly handled

---

## Patch Files

### 0001-fortran-Implement-optional-type-spec-for-DO-CONCURRE.patch
- Author: Jerry DeLisle
- Size: 268 lines (129 insertions, 9 deletions)
- Files: gfortran.h, match.cc, resolve.cc
- Commit: d11074121b3

### 0002-shadow-variable-walker.patch
- Author: Christopher Albert
- Size: ~500 lines (264 insertions, 83 deletions)
- Files: match.cc, resolve.cc
- Commit: b06716ac489

---

## References

- [PR96255](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96255)
- ISO/IEC 1539-1:2010 (Fortran 2008)
- ISO/IEC 1539-1:2018 (Fortran 2018)
- ISO/IEC 1539-1:2023 (Fortran 2023)
