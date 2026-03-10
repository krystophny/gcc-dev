# Bug 102596: ICE on OpenMP task reduction of allocatable scalar

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102596
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/80
- **Branch:** `pr102596-fix`
- **Status:** PENDING (patch on fork branch `origin/pr102596-fix`, commit `aba89bd758f1ddb3d42ca41260b872198ccdc511`)

## Summary

`reduction(task, +:r)` on an allocatable scalar reaches
`gfc_omp_clause_default_ctor` with `outer == NULL_TREE` during `omplower`.
That is valid for scalar allocatables that do not need descriptor copying or
allocatable-component walking, but the Fortran hook asserted on
`outer != NULL_TREE` unconditionally and ICEd before lowering could continue.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fopenmp -c pr/102596/reproducer.f90
```

Expected result after the fix:

- successful compile
- no internal compiler error

## Local Fix

- Keep requiring `outer` for descriptor-based allocatables and for types with
  allocatable components.
- Permit `outer == NULL_TREE` for scalar allocatables that only need plain
  storage allocation in `gfc_omp_clause_default_ctor`.
- Add `gfortran.dg/pr102596.f90` as a regression test for the allocatable
  task-reduction case.

## Validation

- Direct compile of `reproducer.f90`: PASS
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr102596.f90"`:
  PASS
- Full `check-gfortran`:
  PASS (`0` `FAIL`/`XPASS` lines in `gcc-build/gcc/testsuite/gfortran/gfortran.sum`)

## Review Notes

- The fix is narrower than the first attempted `omp-low` change: the middle
  end intentionally has no usable outer reference in this path, so the right
  place to relax the assumption is the Fortran hook itself.

## Patch Artifact

- `pr/102596/0001-fortran-Allow-task-reduction-allocatable-scalars-wit.patch`
