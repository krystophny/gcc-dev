# Bug 120723: OpenACC scalar `attach`/`detach` ICE

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120723
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/96

## Summary

Standalone OpenACC `attach` and `detach` clauses already have dedicated
lowering for pointer components and descriptor-based arrays, but plain scalar
pointer-like variables still fell through the generic scalar pointer mapping
path.  That path generated a standalone pointer-mapping node, and gimplify
then ICEd with `unexpected pointer mapping node`.

## Reproducer

`reproducer.f90`

Compile:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc \
  -I gcc-build/x86_64-pc-linux-gnu/libgomp \
  -fopenacc -c pr/120723/reproducer.f90
```

Expected result after the fix:

- successful compile
- no internal compiler error
