# Bug 120286: OpenMP frees privatized polymorphic pointer targets

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120286
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/95
- **Branch:** `pr120286-fix`
- **Status:** PENDING (patch on fork, full `check-gfortran` PASS)
- **Commit:** `985517a4dcc92c4d8996b9530b6e1beb2333b8fc`

## Summary

For scalar polymorphic pointers in OpenMP `private` and `firstprivate`
clauses, the frontend currently routes the privatized variable through the
same copy/destructor paths as non-pointer polymorphic class objects.  That is
wrong: the privatized pointer should copy only association status and must not
finalize or free the shared target on thread exit.

In the `omplower` dump for the reproducer, the worker function copied
`ptr._vptr` and `ptr._data` from `x%list(n)%p`, then ran a generated cleanup
block that called `_final` and `free(ptr._data)`.  That frees the shared
pointee out from under the program and segfaults on subsequent iterations.

## Reproducer

`reproducer.f90`

Compile and run:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fopenmp pr/120286/reproducer.f90 -o /tmp/pr120286
OMP_NUM_THREADS=2 /tmp/pr120286
```

Expected result after the fix:

- program runs to completion
- no segmentation fault or double free

## Local Fix

- In `gfc_omp_clause_copy_ctor` and `gfc_omp_clause_dtor`, unwrap saved
  descriptors first so the decision is based on the original Fortran entity,
  not on an artificial OpenMP temporary.
- Add a local helper in `trans-openmp.cc` that recognizes class container
  types built for polymorphic pointer entities (`__class_*_p` and array-pointer
  variants).
- Treat associate vars, ordinary scalar pointers, and scalar class-pointer
  containers as association-only state in those two ctor/dtor hooks, without
  changing the global `gfc_is_polymorphic_nonptr` classification used by
  OpenMP mapping warnings and deep-mapping logic.
- Add `gfortran.dg/pr120286.f90`, covering both the original `private(ptr)`
  crash and a `firstprivate(ptr)` association check.

## Validation

- Direct compile and run of `reproducer.f90`: PASS
- Direct `-fdump-tree-omplower` review: PASS (privatized worker no longer emits
  finalize/free cleanup for `ptr`)
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr120286.f90"`:
  PASS
- Warning regression check:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=gomp/polymorphic-mapping-1.f90"`:
  PASS
- Full `check-gfortran`: PASS (`0` `FAIL`/`XPASS`)

## Review Notes

- The key fix is classification in the privatization hooks, not cleanup logic:
  scalar class pointers were being misrouted through the non-pointer
  polymorphic ctor/dtor path.
- The class-pointer helper is intentionally local to those hooks.  A broader
  change to `gfc_is_polymorphic_nonptr` suppressed existing OpenMP
  polymorphic-mapping warnings and was rejected during self-review.
