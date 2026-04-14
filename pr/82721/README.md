# Bug 82721: Corrupted error message / ICE after duplicate type

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82721
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/56

## Summary

`CHARACTER(len(...))` declarations allocate `gfc_charlen` nodes on the current
namespace while parsing the type-spec.  If the declaration is later rejected
because the symbol was already declared with a different type, those fresh
charlen nodes survive statement rollback.  Resolution later walks the stale
`len(c)` expression and can produce corrupted diagnostics or segfault.

## Reproducer

`reproducer.f90`

Compile command:

```bash
MALLOC_PERTURB_=165 gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only \
  pr/82721/reproducer.f90
```

Expected result after the fix:

- diagnostic about the duplicate declaration
- no internal compiler error
