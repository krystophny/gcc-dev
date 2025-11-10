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
| **GCC gfortran (15.2.1)** | `Error: Unexpected data declaration statement at (1)` | ❌ Generic, unhelpful |
| **GCC gfortran (16.0.0 dev)** | `Error: Unexpected data declaration statement at (1)` | ❌ Generic, unhelpful |
| **Intel ifx** | `error #6236: A specification statement cannot appear in the executable section.` | ✅ Clear, educational |
| **NVIDIA nvfortran** | `NVFORTRAN-S-0070-Incorrect sequence of statements` | ⚠️ Vague but better than GCC |
| **LLVM Flang** | `error: misplaced declaration in the execution part` | ✅ Clear, specific |
| **LFortran** | (No error - accepts the code) | ❌ Misses the error entirely |

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
| **GCC gfortran (15.2.1)** | `Error: Unexpected COMMON statement at (1)` | ❌ Generic, unhelpful |
| **GCC gfortran (16.0.0 dev)** | `Error: Unexpected COMMON statement at (1)` | ❌ Generic, unhelpful |
| **Intel ifx** | `error #6236: A specification statement cannot appear in the executable section.` | ✅ Clear, educational |
| **NVIDIA nvfortran** | `NVFORTRAN-S-0070-Incorrect sequence of statements` | ⚠️ Vague but better than GCC |
| **LLVM Flang** | `error: misplaced declaration in the execution part` | ✅ Clear, specific |
| **LFortran** | (No error - accepts the code) | ❌ Misses the error entirely |

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
| **GCC gfortran (15.2.1)** | `Error: Unexpected !$OMP THREADPRIVATE statement at (1)` | ❌ Generic, unhelpful |
| **GCC gfortran (16.0.0 dev)** | `Error: Unexpected !$OMP THREADPRIVATE statement at (1)` | ❌ Generic, unhelpful |
| **Intel ifx** | `error #6236: A specification statement cannot appear in the executable section.` | ✅ Clear, educational |
| **NVIDIA nvfortran** | (No error - accepts the code) | ⚠️ Inconsistent |
| **LLVM Flang** | `error: misplaced declaration in the execution part`<br>`error: expected OpenMP construct` | ✅ Clear, specific |
| **LFortran** | (No error - accepts the code) | ❌ Misses the error entirely |

## Analysis Summary

### Comprehensive Compiler Assessment

**🏆 Best Error Messages:**
1. **Intel ifx** - Consistently excellent across all test cases
   - Clear: "A specification statement cannot appear in the executable section."
   - Educational: Explains the underlying Fortran language rule
   - Consistent: Same message format for all specification statements
   - User-friendly: Helps programmers understand Fortran statement ordering

2. **LLVM Flang** - Very good error messages
   - Clear: "misplaced declaration in the execution part"
   - Specific: Points to exact location and context
   - Detailed: Provides hierarchical context information

**⚠️ Mixed Results:**
3. **NVIDIA nvfortran** - Acceptable but vague
   - Generic: "Incorrect sequence of statements"
   - Better than GCC but lacks specificity
   - Inconsistent: Sometimes doesn't detect OpenMP threadprivate errors

**❌ Poor Error Messages:**
4. **GCC gfortran (both versions)** - Generic and unhelpful
   - Generic: "Unexpected X statement at (1)"
   - Educational value: None
   - Consistent problems across all specification statement types
   - Same poor quality in both stable (15.2.1) and development (16.0.0) versions

5. **LFortran** - Misses errors entirely
   - Critical: Accepts invalid Fortran code without complaint
   - Standards compliance issue: Doesn't enforce statement ordering
   - Development stage: May need more compiler validation work

### Problems with Current GCC Messages

1. **Generic pattern:** "Unexpected X statement at (1)"
   - Doesn't explain *why* the statement is unexpected
   - Doesn't teach Fortran statement ordering rules
   - Confusing for new Fortran programmers
   - Same issue persists across 15+ years of development

2. **No improvement over time:**
   - Identical error messages in GCC 15.2.1 and 16.0.0
   - Bug 32365 remains unfixed since 2007

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

## Complete Error Message Reference

### Detailed Compiler Output - Test Case 1 (Variable Declaration)

**GCC 15.2.1 & 16.0.0:**
```
simple_spec.f90:5:18:
      5 |       integer :: j
        |                  1
Error: Unexpected data declaration statement at (1)
simple_spec.f90:6:7:
      6 |       j = 2
        |       1
Error: Symbol 'j' at (1) has no IMPLICIT type
```

**Intel ifx:**
```
simple_spec.f90(5): error #6236: A specification statement cannot appear in the executable section.
      integer :: j
------^
simple_spec.f90(6): error #6404: This name does not have a type, and must have an explicit type.   [J]
      j = 2
------^
compilation aborted for simple_spec.f90 (code 1)
```

**NVIDIA nvfortran:**
```
NVFORTRAN-S-0070-Incorrect sequence of statements  (simple_spec.f90: 5)
  0 inform,   0 warnings,   1 severes, 0 fatal for test
```

**LLVM Flang:**
```
error: Could not parse simple_spec.f90
./simple_spec.f90:5:19: error: misplaced declaration in the execution part
        integer :: j
                    ^
./simple_spec.f90:5:7: in the context: execution part construct
        integer :: j
        ^
./simple_spec.f90:4:7: in the context: execution part
        i = 1
        ^
```

**LFortran:**
```
(No error - accepts the code successfully)
```

### OpenMP Threadprivate - LLVM Flang Detailed Output

```
error: Could not parse simple_omp.f90
./simple_omp.f90:5:23: error: misplaced declaration in the execution part
  !$omp threadprivate(a)
                        ^
./simple_omp.f90:5:1: in the context: execution part construct
  !$omp threadprivate(a)
  ^
./simple_omp.f90:4:7: in the context: execution part
        a = 1
        ^
./simple_omp.f90:5:23: error: expected OpenMP construct
  !$omp threadprivate(a)
                        ^
./simple_omp.f90:5:1: in the context: OpenMP construct
  !$omp threadprivate(a)
  ^
./simple_omp.f90:4:7: in the context: execution part
        a = 1
        ^
```

### Key Insights from Complete Comparison

1. **Intel ifx** provides the most educational and consistent experience
2. **LLVM Flang** offers detailed contextual information but verbose output
3. **GCC** remains stuck with generic, unhelpful messages across both stable and development versions
4. **NVIDIA nvfortran** has basic detection but lacks specificity
5. **LFortran** fails to detect fundamental Fortran statement ordering rules

This comprehensive analysis demonstrates that GCC significantly lags behind other modern Fortran compilers in user experience and educational value.