# Bug 102596: ICE on OpenMP task reduction of allocatable scalar

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102596
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/80

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
