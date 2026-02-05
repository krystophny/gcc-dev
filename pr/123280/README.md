# Bug 96080 + 123280: OpenACC Fortran runtime routines vs assumed-shape/pointers

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96080
- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123280
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/12
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/13
- **Branch:** `pr123280-fix` (also on integration branch `openacc`)
- **Status:** PENDING (patch on fork, awaiting upstream submission)
- **Note:** Single patch fixes both PRs

## Summary

All OpenACC Fortran runtime library routines with assumed-rank dummy arguments
fail when called with assumed-shape dummy arguments or Fortran pointers.
This affects `acc_copyin`, `acc_create`, `acc_copyout`, `acc_delete`,
`acc_is_present`, `acc_update_device`, `acc_update_self`, and all their
async/finalize variants.

As noted by Thomas Schwinge in PR96080 comment #1: the problem is "not
specific to just `acc_is_present`, but probably all (?) OpenACC/Fortran
runtime library routines."

## Root Cause

All `_array_h` routines in `libgomp/openacc.f90` had `contiguous` on their
assumed-rank dummy argument:

```fortran
subroutine acc_copyin_array_h (a)
  type (*), dimension (..), contiguous :: a  ! <-- contiguous forces copy
```

When a non-contiguous array (assumed-shape dummy, Fortran pointer) was passed,
gfortran created a temporary copy. The runtime then operated on the copy's
address rather than the original data:

- `acc_is_present`: returned false for data actually present on device
- `acc_copyin`/`acc_create`: mapped a temporary freed after the call
- `acc_copyout`/`acc_delete`: failed to find the original mapping

## Fix

Remove `contiguous` from all 36 affected declarations (18 interface + 18
implementation). These routines only pass the base address and `sizeof(a)`
to the underlying C functions, so contiguous storage is not required.

## Test Results

| Compiler | Test 1 (direct) | Test 2 (assumed-shape) |
|----------|-----------------|------------------------|
| nvfortran 25.11 | PASS | PASS |
| GCC 16.0.0 (before fix) | PASS | FAIL |
| GCC 16.0.0 (after fix) | PASS | PASS |

GPU runtime test with NVPTX offload: PASS

## Build & Run

```bash
OFFLOAD=$PWD/gcc-offload-build/install

# GCC (shows bug with unpatched libgomp)
$OFFLOAD/bin/gfortran -fopenacc -foffload=nvptx-none -o reproducer reproducer.f90
LD_LIBRARY_PATH=$OFFLOAD/lib64 ./reproducer

# nvfortran (works correctly)
nvfortran -acc -o reproducer_nv reproducer.f90
./reproducer_nv
```
