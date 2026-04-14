# Bug 123943: DO CONCURRENT nested-in-block iterator counting ICE

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123943

## Summary

GCC 16 regressed when `DO CONCURRENT` iterator counting walked nested
`BLOCK` scopes incorrectly and could ICE in `gfc_resolve_forall`.

## Reproducer

`reproducer.f90`
Compile command:
```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -c pr/123943/reproducer.f90 -o /dev/null
```
Expected result after the fix:
- successful compile
- no internal compiler error

## Fix

- Correct iterator counting for nested `BLOCK` namespaces when resolving
  `FORALL` / `DO CONCURRENT` constructs.
- Keep the change scoped to the iterator walk used for `var_expr` sizing.
