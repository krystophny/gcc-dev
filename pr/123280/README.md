# Bug 123280 + 96080: acc_is_present fails for assumed-shape and pointers

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123280
- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96080
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/12
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/13
- **Status:** PENDING (patch on fork, awaiting upstream submission)
- **Note:** Single patch fixes both PRs

## Summary

`acc_is_present()` fails to detect mapped data when called with:
- Assumed-shape dummy arguments (PR 123280)
- Fortran pointers to mapped targets (PR 96080)

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
