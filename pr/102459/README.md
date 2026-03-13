# Bug 102459: ICE on OpenMP iterator depend clause with component array

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102459
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/79
- **Branch:** `pr102459-fix`
- **Status:** MERGED (r16-8070-gd2ab04fbba7b9)

## Summary

`!$omp task depend(iterator(...), out:x(j)%a)` reaches
`gfc_trans_omp_clauses` with an expression whose first reference is the scalar
base element `x(j)`, but whose overall value is still the rank-1 component
array `a`.  The current lowering decides between the scalar reference path and
the array descriptor path by inspecting only that first `REF_ARRAY`, so it
incorrectly calls `gfc_conv_expr_reference` on an array-valued expression.
That later falls into `gfc_conv_scalarized_array_ref` without scalarizer state
and ICEs on `se->ss == NULL`.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fopenmp -fsyntax-only \
  pr/102459/reproducer.f90
```

Expected result after the fix:

- compile succeeds
- no internal compiler error

## Local Fix

- In `gfc_trans_omp_clauses`, choose the scalar/reference path from
  `n->expr->rank == 0` instead of `n->expr->ref->u.ar.type == AR_ELEMENT`.
- This preserves the scalar handling for expressions like `x(j)%a(1)` but
  sends array-valued expressions like `x(j)%a` through
  `gfc_conv_expr_descriptor`.
- Apply the same rank-based decision in `gfc_trans_omp_depobj`, which used the
  same first-ref test.
- Add `gfortran.dg/pr102459.f90`, covering the original `x(j)%a` reproducer and
  a scalar control case `x(j)%a(1)`.

## Validation

- Direct compile of `reproducer.f90`: PASS
- Direct compile of scalar control variant `x(j)%a(1)`: PASS
- Direct `-O -S` compile of both variants: PASS
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr102459.f90"`:
  PASS
- Full `check-gfortran`:
  PASS (`0` `FAIL`/`XPASS` lines in `gcc-build/gcc/testsuite/gfortran/gfortran.sum`)

## Review Notes

- The fix is intentionally narrow: only the scalar-vs-array decision changes.
- The regression test stays on `task depend`; adding a `depobj` iterator test
  exposed a separate `-O`-only ICE in `gimplify`, so that coverage belongs to a
  different follow-up bug rather than this patch.

## Patch Artifact

- `pr/102459/0001-fortran-Fix-OpenMP-iterator-depend-lowering-for-comp.patch`
