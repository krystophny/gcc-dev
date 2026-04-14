# PR96255: Fortran DO CONCURRENT Type-Spec Implementation

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96255
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/1

**Upstream Commits:**
- 5e62a23cc3a - fortran: Implement optional type spec for DO CONCURRENT [PR96255]
- 0ef98bf3351 - Fortran: Remove unused variable. [PR 96255]
- 1099ffffffe - Fortran: Mark type-spec iterators referenced
- a892a2dac6b - Fortran: Remove dg-bogus from test case

**Test Results:** All tests passing (0 unexpected failures)

---

## Overview

This PR implements support for the optional Fortran 2008 integer type specification in DO CONCURRENT and FORALL headers:

```fortran
do concurrent (integer(kind=4) :: i = 1:10)
  result(i) = real(i) * 2.0
end do
```

**MERGED:** Upstream as commits 5e62a23cc3a (main implementation), 0ef98bf3351 (unused variable cleanup), 1099ffffffe (mark iterators referenced), a892a2dac6b (test cleanup). Bugzilla RESOLVED FIXED 2025-11-13.

The implementation is split between two major patches:

1. **Base Implementation (5e62a23cc3a)**: Parsing, shadow variable creation, data structures
2. **Follow-up Fixes (1099ffffffe)**: Iterator marking, reference tracking, optimization

---

## Part 1: Base Implementation (5e62a23cc3a)

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

## Part 2: Iterator Marking and Reference Tracking (1099ffffffe)

### Upstream Fix: Mark type-spec iterators referenced

**Purpose:** Ensures type-spec iterator variables are properly marked as "referenced" so the compiler tracks them correctly.

**Implementation (resolve.cc):**
- Marks iterator variables created by type-specs as referenced
- Prevents spurious "unused variable" warnings
- Ensures proper symbol resolution and optimization

**What it does:**
When a DO CONCURRENT has a type-spec that creates a new local iterator with a specific type, this fix ensures the compiler knows the iterator is actually being used (rather than marked as unused). This is critical for proper code generation and diagnostics.

**Example:**
```fortran
integer :: i
do concurrent (integer(kind=8) :: i = 1:10)  ! Iterator i is marked referenced
  print *, i  ! Prevents "i is unused" warning
end do
```

---

## Original Implementation Details (Reference)

### Shadow Variable Mechanism

When type-spec differs from outer scope variable:
- Creates new symbol with `_` prefix (e.g., `_i` for iterator `i`)
- Sets `iter->shadow = true` flag
- Converts iterator bounds to specified type
- Replaces all references in loop body with shadow variable

Purpose: Avoids type conflicts when DO CONCURRENT type-spec differs from outer scope variable kind.

### F2008 Constraint Enforcement

`gfc_do_concurrent_flag` states:
- 0 = Outside DO CONCURRENT
- 1 = Inside DO CONCURRENT body (only PURE procedures allowed)
- 2 = Inside DO CONCURRENT mask (impure functions like SUM allowed)

Enforces F2008 constraint C1139: only PURE procedures allowed in DO CONCURRENT body.

### Reduction Semantics in DO CONCURRENT

DO CONCURRENT and FORALL have different semantics:
- **FORALL**: Strict iteration independence required
- **DO CONCURRENT**: "Arbitrary order execution" (more permissive)

All major compilers (Intel ifx, NVIDIA nvfortran, HPE cce) have always allowed reductions in DO CONCURRENT. Fortran 2023's REDUCE locality-spec formalizes this existing practice.

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

## Upstream Commits

### Main Implementation (5e62a23cc3a)
- fortran: Implement optional type spec for DO CONCURRENT [PR96255]
- Files: gfortran.h, match.cc, resolve.cc
- Added type-spec parsing and shadow variable creation

### Remove Unused Variable (0ef98bf3351)
- Fortran: Remove unused variable. [PR 96255]
- Cleanup of unused variable introduced in main implementation

### Mark Iterators Referenced (1099ffffffe)
- Fortran: Mark type-spec iterators referenced
- Files: resolve.cc
- Ensures proper reference tracking for iterators

### Remove dg-bogus from Test (a892a2dac6b)
- Fortran: Remove dg-bogus from test case
- Test cleanup after iterator marking fix made dg-bogus unnecessary

## Local Patch Files (for reference/archival)

- 0001-fortran-Implement-optional-type-spec-for-DO-CONCURRE.patch
- 0001-fortran-Mark-type-spec-iterators-referenced.patch

---

## References

- [PR96255](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96255)
- ISO/IEC 1539-1:2010 (Fortran 2008)
- ISO/IEC 1539-1:2018 (Fortran 2018)
- ISO/IEC 1539-1:2023 (Fortran 2023)
