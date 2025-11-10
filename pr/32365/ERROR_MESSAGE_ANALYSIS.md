# Error Message Analysis - GCC Bug 32365

## Current Error Message Comparison

### Test Case 1: Variable Declaration in Executable Section
**File:** `simple_spec.f90`
```fortran
subroutine test
      implicit none
      integer :: i
      i = 1           ! First executable statement
      integer :: j     ! Specification statement after executable
      j = 2
end subroutine test
```

| Compiler | Error Message | Quality Assessment |
|----------|---------------|-------------------|
| **GCC gfortran** | `Error: Unexpected data declaration statement at (1)` | ❌ Generic, unhelpful |
| **Intel ifx** | `error #6236: A specification statement cannot appear in the executable section.` | ✅ Clear, educational |
| **NVIDIA nvfortran** | `NVFORTRAN-S-0070-Incorrect sequence of statements` | ⚠️ Vague but better than GCC |

### Test Case 2: COMMON Statement in Executable Section
**File:** `common_test.f90`
```fortran
subroutine test_common
      implicit none
      integer :: i
      i = 1           ! First executable statement
      common /myi/ i  ! Specification statement after executable
end subroutine test_common
```

| Compiler | Error Message | Quality Assessment |
|----------|---------------|-------------------|
| **GCC gfortran** | `Error: Unexpected COMMON statement at (1)` | ❌ Generic, unhelpful |
| **Intel ifx** | `error #6236: A specification statement cannot appear in the executable section.` | ✅ Clear, educational |
| **NVIDIA nvfortran** | `NVFORTRAN-S-0070-Incorrect sequence of statements` | ⚠️ Vague but better than GCC |

### Test Case 3: OpenMP Threadprivate in Executable Section
**File:** `simple_omp.f90`
```fortran
subroutine test
      implicit none
      integer :: a
      a = 1                   ! First executable statement
!$omp threadprivate(a)       ! Specification statement after executable
end subroutine test
```

| Compiler | Error Message | Quality Assessment |
|----------|---------------|-------------------|
| **GCC gfortran** | `Error: Unexpected !$OMP THREADPRIVATE statement at (1)` | ❌ Generic, unhelpful |
| **Intel ifx** | `error #6236: A specification statement cannot appear in the executable section.` | ✅ Clear, educational |
| **NVIDIA nvfortran** | (No error - possibly different handling) | ⚠️ Inconsistent |

## Analysis Summary

### Problems with Current GCC Messages

1. **Generic pattern:** "Unexpected X statement at (1)"
   - Doesn't explain *why* the statement is unexpected
   - Doesn't teach Fortran statement ordering rules
   - Confusing for new Fortran programmers

2. **Inconsistent messaging:**
   - Some statements get "Unexpected" prefix
   - Others may have different error handling
   - No unified approach to specification vs executable statements

### Intel's Superior Approach

Intel ifx consistently provides:
```
error #6236: A specification statement cannot appear in the executable section.
```

**Benefits:**
- ✅ Explains the underlying Fortran language rule
- ✅ Educational for users learning Fortran
- ✅ Consistent across different specification statements
- ✅ Helps users understand statement ordering requirements

### Technical Implementation Notes

From the bug discussion, key insights:

1. **Jakub Jelinek (2007-06-20):** Suggested adding specific case handling in `parse_executable`
2. **Tobias Burnus (2007-06-20):** Noted that `verify_st_order` has better messaging but may not be called consistently
3. **Daniel Franke (2009-12-11):** Confirmed that `verify_st_order` is not called for every accepted statement

### Recommendations

1. **Primary:** Implement Intel-style error messages in GCC
   - Target message: "A specification statement cannot appear in the executable section."
   - Apply consistently to all specification statements after executable statements

2. **Secondary:** Investigate `verify_st_order` consistency
   - Ensure it's called for all statement types
   - May provide better infrastructure for statement ordering validation

3. **Affected statement types:**
   - Variable declarations (`integer :: x`)
   - COMMON statements
   - OpenMP threadprivate directives
   - Other specification constructs (PARAMETER, SAVE, etc.)

### Implementation Strategy

1. **Locate rejection point:** Find where "Unexpected X statement" errors are generated
2. **Add specific handling:** Detect specification statements after executable statements begin
3. **Implement better messages:** Use clear, educational error text
4. **Ensure consistency:** Apply to all affected statement types
5. **Test regressions:** Verify no breakage in existing error handling

This enhancement would significantly improve GCC's user-friendliness for Fortran developers while maintaining technical accuracy.