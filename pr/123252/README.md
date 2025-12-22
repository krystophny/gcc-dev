# PR123252 - OpenACC: derived-type scalar reads wrong on device

**Title:** OpenACC: derived-type scalar component has wrong value in device
kernel when only array component is mapped

**Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123252

**Component:** fortran (OpenACC)

**Status:** UNCONFIRMED (Bugzilla); tracked locally for reproduction.

**Tracking issue:** https://github.com/krystophny/gcc-dev/issues/11

## Summary

Mapping only an allocatable array component of a derived type with OpenACC
(`enter data copyin(c%arr(...))`) and then reading a scalar component (`c%flag`)
in a device kernel can yield the wrong result: the device observes `c%flag` as
false/garbage and takes the wrong branch.

The reproducer is `reproducer.f90`.  It prints `PASS` when `c%flag` is observed
as true on the device and prints `FAIL` and exits non-zero otherwise.

## How to run

This is a runtime offload issue; compile-only testing is not sufficient.

Example build/run:

```bash
gfortran -O2 -fopenacc -foffload=nvptx-none pr/123252/reproducer.f90 -o /tmp/pr123252.x
ACC_DEVICE_TYPE=nvidia /tmp/pr123252.x
```

## Evidence (local)

Built and ran with NVPTX offloading using the local trunk toolchain; logs:

- Build: `/tmp/pr123252_nvptx_build_2025-12-22.log`
- Run: `/tmp/pr123252_nvptx_run_2025-12-22.log`

## Patch (local)

Exported from `gcc` repo:

- `0001-gimplify-map-Fortran-DT-scalars-for-OpenACC-enter-da.patch`

## Verification (local)

After applying the patch and rebuilding/installing the NVPTX offload toolchain:

- `pr/123252/reproducer.f90` prints `PASS` with `ACC_DEVICE_TYPE=nvidia`:
  `/tmp/pr123252_after_pr123255_fix_run.log`
- OpenACC/OpenMP NVPTX smoke tests:
  `/tmp/pr123255_fix_openacc_smoke.log`, `/tmp/pr123255_fix_openmp_smoke.log`

This patch also includes a field-ordering fix for Fortran derived types with
descriptors and adds a compile-only regression for that ordering (PR123255):

- `gcc/testsuite/gfortran.dg/goacc/pr123255-allocatable-component-map-order.f90`
