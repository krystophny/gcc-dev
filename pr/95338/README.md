# Bug 95338: ICE on mixed ENTRY result types with `-ff2c`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95338
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/68

## Summary

For mixed `ENTRY` functions, the frontend builds a master union result that
stores one field per entry result.  Under `-ff2c`, default `REAL` entries use
the C `double` ABI return type even though their Fortran result symbol remains
default `REAL`.  The union builder currently uses the Fortran symbol type
directly, so the master union stores a `real(kind=4)` field while the entry
wrapper returns `real(kind=8)`.  That leaves a non-trivial conversion inside a
`COMPONENT_REF`, and the GIMPLE verifier rejects the lowered code.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -O1 -ff2c -c pr/95338/reproducer.f90
```

Expected result after the fix:

- successful compile
- no internal compiler error
