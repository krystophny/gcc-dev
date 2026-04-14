# Bug 102459: ICE on OpenMP iterator depend clause with component array

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102459
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/79

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
