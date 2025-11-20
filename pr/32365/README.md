# GCC Bug 32365 - Better error message for specification statement in executable section

**Status:** RESOLVED FIXED (merged in gcc commit 7db49bf4be2 on 2025-11-17)
**Component:** fortran
**Version:** 4.3.0 (original report)
**Importance:** P3 enhancement
**Reported:** 2007-06-16 by Tobias Burnus
**Last modified:** 2025-11-19 (Bugzilla closed)

## Description

The issue requests better error messages when specification statements appear in the executable section of a Fortran program. Currently, gfortran gives generic "Unexpected X statement" errors, while other compilers provide more descriptive messages indicating the specific problem (specification statements in executable section).

## Current Behavior Comparison

### Test Case: `simple_spec.f90`
```fortran
subroutine test
      implicit none
      integer :: i
      i = 1
      integer :: j  ! Specification statement after executable statement
      j = 2
end subroutine test
```

### Compiler Error Messages:

**GCC/gfortran:**
```
simple_spec.f90:5:18:
      5 |       integer :: j
        |                  1
Error: Unexpected data declaration statement at (1)
```

**Intel ifx:**
```
simple_spec.f90(5): error #6236: A specification statement cannot appear in the executable section.
      integer :: j
------^
```

**NVIDIA nvfortran:**
```
NVFORTRAN-S-0070-Incorrect sequence of statements  (simple_spec.f90: 5)
```

### Test Case: OpenMP Threadprivate

**GCC/gfortran:**
```
reproducer.f90:8:22:
      8 | !$omp threadprivate(a)
        |                      1
Error: Unexpected !$OMP THREADPRIVATE statement at (1)
```

**Intel ifx (expected from bug report):**
```
Error: A specification statement cannot appear in the executable section.
```

## Resolution (2025-11-17)

- Upstream commit `7db49bf4be2` (Jerry DeLisle, signed-off by Christopher Albert) enforces the rule in `parse_executable` that specification and OpenMP directive statements appearing after executable code are rejected with a precise diagnostic.
- New regression `gcc/testsuite/gfortran.dg/spec_statement_in_exec.f90` covers DATA/COMMON/NAMELIST/OpenMP cases under `-fopenmp` and updates a dozen OpenMP/GACC tests to the stricter wording.
- Behavior now matches reference compilers (ifx, nvfortran) and gives users a clear "specification statement cannot appear in the executable section" message.

## Analysis (historic)

### Current GCC Error Messages
- Generic: "Unexpected X statement at (1)"
- Low specificity, doesn't explain *why* the statement is unexpected
- Doesn't help users understand Fortran statement ordering rules

### Better Error Messages (from other compilers)
- Intel: "A specification statement cannot appear in the executable section."
- Clear, specific, and educational
- Explains the underlying Fortran language rule

### Root Cause
The issue appears to be in `parse_executable` function in `parse.c` where the default case simply returns the statement without providing specific error messages for specification statements that appear after executable statements have begun.

### Proposed Solution (from bug comments)
Jakub Jelinek suggested adding specific error handling in `parse_executable`:

```c
case_decl:
  gfc_error ("%s statement can't appear after the first executable statement at %C",
             gfc_ascii_statement (st));
  reject_statement ();
  break;
```

However, Tobias Burnus noted that `verify_st_order` in `parse.c` already has better error messaging but may not be called consistently.

## Technical Investigation Required

1. **Locate the exact code path** where specification statements are rejected
2. **Determine why `verify_st_order` is not called consistently** (as noted by Daniel Franke)
3. **Identify all affected statement types** (not just OpenMP threadprivate)
4. **Implement improved error messages** that match Intel's clarity
5. **Ensure no regression** in existing error handling

## Files Created

- `reproducer.f90` - Original OpenMP threadprivate reproducer from bug report
- `common_test.f90` - Additional test case with COMMON statement in executable section
- `simple_spec.f90` - Minimal test case with variable declaration in executable section
- `Makefile` - Comprehensive testing with multiple compilers
- `README.md` - This documentation

## Testing

Run comprehensive tests with:
```bash
make all
```

This will test all reproducers with:
- Custom gfortran build (if available)
- System gfortran
- Intel ifx
- NVIDIA nvfortran

## Expected Enhancement

After fixing, GCC should produce error messages similar to:
- "A specification statement cannot appear in the executable section."
- "COMMON statement cannot appear after the first executable statement"
- "!$OMP THREADPRIVATE statement cannot appear after the first executable statement"

This would make the compiler more user-friendly and help Fortran programmers understand statement ordering requirements.
