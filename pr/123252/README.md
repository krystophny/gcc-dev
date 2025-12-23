# PR123252 - OpenACC: derived-type scalar reads wrong on device

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123252
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/11
- **Status:** PENDING (patch on fork, awaiting upstream submission)

**Title:** OpenACC: derived-type scalar component has wrong value in device
kernel when only array component is mapped

**Component:** fortran (OpenACC)

## Summary

When an OpenACC enter data maps only an allocatable component of a Fortran
derived type (for example `enter data copyin(c%arr(...))`), gimplify still
creates a `GOMP_MAP_STRUCT` mapping for the enclosing derived object.  Before
this change, that struct mapping did not also copy scalar, non-pointer
components such as `c%flag` or `c%n`, so later device kernels could read those
scalar fields as garbage and take the wrong branch.

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

Exported from `gcc` repo, v3 (frontend fix in trans-openmp.cc):

- `0001-fortran-Map-scalar-fields-on-OpenACC-enter-data-PR12.patch`

Previous approaches (gimplify.cc) did not work because GOMP_MAP_TO_PSET clauses
skip the call to omp_accumulate_sibling_list where scalar field synthesis was
attempted.  The current approach adds scalar field synthesis directly in the
Fortran frontend (trans-openmp.cc), similar to the PR 103276 fix.

## Verification (local)

Compile-only regression test passes:

```
PASS: gfortran.dg/goacc/pr123252.f90   -O  (test for excess errors)
PASS: gfortran.dg/goacc/pr123252.f90   -O   scan-tree-dump omplower "map\(to:c\.flag"
PASS: gfortran.dg/goacc/pr123252.f90   -O   scan-tree-dump omplower "map\(to:c\.n"
```

All goacc tests pass (3950 expected passes, 281 expected failures).
