# Bug 123280: acc_is_present fails for assumed-shape dummy argument

- **URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123280
- **Status:** FIXED (patch ready)
- **Related:** Bug 96080 (similar issue with Fortran pointers)

## Summary

When an array is mapped to the device by a caller using OpenACC directives, and then
passed to a subroutine as an assumed-shape dummy argument, `acc_is_present()` inside
the subroutine fails to detect that the data is present on the device.

## Root Cause

The `acc_is_present_array_h` function in libgomp/openacc.f90 had `contiguous` on its
assumed-rank dummy argument:

```fortran
function acc_is_present_array_h (a)
  type (*), dimension (..), contiguous :: a  ! <-- contiguous forces copy
```

When an assumed-shape array (like `x(:)`) was passed, gfortran created a temporary
copy to satisfy the contiguity requirement. The lookup then checked the address of
the temporary, not the original mapped data.

## Fix

Remove `contiguous` from `acc_is_present_array_h`. The function only needs the base
address and size for the runtime lookup, not a guarantee of contiguous storage.

## Test Results

| Compiler | Test 1 (direct) | Test 2 (assumed-shape) |
|----------|-----------------|------------------------|
| nvfortran 25.11 | PASS | PASS |
| GCC 16.0.0 (before fix) | PASS | FAIL |
| GCC 16.0.0 (after fix) | PASS | PASS |

## Build & Run

```bash
# GCC (shows bug with unpatched libgomp)
gfortran -fopenacc -foffload=nvptx-none -o reproducer reproducer.f90
./reproducer

# nvfortran (works correctly)
export NVHPC_CUDA_HOME=/opt/cuda
nvfortran -acc -o reproducer_nv reproducer.f90
./reproducer_nv
```
