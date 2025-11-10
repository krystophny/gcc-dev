# GCC Version Comparison - Bug 32365 Analysis

## Current GCC Versions Tested

### System GCC (Ubuntu Package)
- **Version:** GNU Fortran (GCC) 15.2.1 20250813
- **Source:** Ubuntu package manager
- **Status:** Stable release

### Custom GCC Build
- **Version:** GNU Fortran (GCC) 16.0.0 20251109 (experimental)
- **Source:** Built from `/home/ert/code/gcc-dev/gcc/`
- **Status:** Development/Trunk version

## Error Message Comparison

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

| GCC Version | Error Message | Status |
|-------------|---------------|--------|
| **GCC 15.2.1 (System)** | `Error: Unexpected data declaration statement at (1)`<br>`Error: Symbol 'j' at (1) has no IMPLICIT type` | ❌ Generic, unhelpful |
| **GCC 16.0.0 (Dev)** | `Error: Unexpected data declaration statement at (1)`<br>`Error: Symbol 'j' at (1) has no IMPLICIT type` | ❌ Same generic message |

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

| GCC Version | Error Message | Status |
|-------------|---------------|--------|
| **GCC 15.2.1 (System)** | `Error: Unexpected COMMON statement at (1)` | ❌ Generic, unhelpful |
| **GCC 16.0.0 (Dev)** | `Error: Unexpected COMMON statement at (1)` | ❌ Same generic message |

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

| GCC Version | Error Message | Status |
|-------------|---------------|--------|
| **GCC 15.2.1 (System)** | `Error: Unexpected !$OMP THREADPRIVATE statement at (1)` | ❌ Generic, unhelpful |
| **GCC 16.0.0 (Dev)** | `Error: Unexpected !$OMP THREADPRIVATE statement at (1)` | ❌ Same generic message |

## Key Findings

### No Improvement in GCC 16.0.0
- **Status:** Bug 32365 remains UNFIXED in current development trunk
- **Error messages:** Identical between GCC 15.2.1 and 16.0.0
- **Pattern:** Consistent "Unexpected X statement at (1)" format across all test cases

### Persistent Issues
1. **Generic error pattern:** "Unexpected X statement at (1)"
2. **No educational value:** Doesn't explain Fortran statement ordering rules
3. **Missing context:** Doesn't help users understand *why* the statement is unexpected
4. **Consistent poor UX:** Same quality issues across all specification statement types

### Comparison with Other Compilers (Reference)

**Intel ifx:** `error #6236: A specification statement cannot appear in the executable section.`
- ✅ Clear, educational message
- ✅ Explains the underlying Fortran rule
- ✅ Consistent across specification statement types

**NVIDIA nvfortran:** `NVFORTRAN-S-0070-Incorrect sequence of statements`
- ⚠️ Better than GCC but still somewhat vague

### Technical Implications

Since the error messages are identical between GCC 15.2.1 (stable) and GCC 16.0.0 (development), this confirms:

1. **No progress made** on this enhancement since the bug was reported in 2007
2. **Development opportunity** exists for improving user experience
3. **Clear implementation path** based on Intel's superior approach
4. **Consistent error handling** needed across all specification statements

### Recommended Enhancement

Both GCC versions should be enhanced to provide Intel-style error messages:
```
"A specification statement cannot appear in the executable section."
```

This would significantly improve the user experience for Fortran developers learning proper statement ordering.

## Testing Commands Used

```bash
# System GCC 15.2.1
/usr/bin/gfortran -c simple_spec.f90
/usr/bin/gfortran -c common_test.f90
/usr/bin/gfortran -fopenmp -c simple_omp.f90

# Custom GCC 16.0.0
/home/ert/code/gcc-dev/gcc-build/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build/gcc -c simple_spec.f90
/home/ert/code/gcc-dev/gcc-build/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build/gcc -c common_test.f90
/home/ert/code/gcc-dev/gcc-build/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build/gcc -fopenmp -c simple_omp.f90
```

## Conclusion

Bug 32365 represents a significant user experience improvement opportunity that has remained unaddressed for over 15 years. The enhancement would make GCC Fortran more beginner-friendly and align it with industry best practices for compiler error messaging.