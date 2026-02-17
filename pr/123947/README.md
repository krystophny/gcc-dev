# Bug 123947: [16 regression] ICE in `gfc_build_addr_expr` at `trans.cc:350`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123947
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/48
- **Status:** UNCONFIRMED upstream (last modified 2026-02-11), tracked locally

## Summary

GCC 16 trunk crashes with an ICE (`Segmentation fault`) while compiling a
small recursive-type testcase. The stack trace points to:

- `contains_struct_check` (`tree.h`)
- `gfc_build_addr_expr` (`gcc/fortran/trans.cc:350`)

Reported behavior in Bugzilla:

- `gfortran 15.2.0`: compiles testcase
- `gfortran trunk (2026-01-02 and 2026-01-31 snapshots)`: ICE

## Reproducer

Reduced testcase from Bugzilla attachment 63567 is stored in:

- `pr/123947/reproducer.f90`

Compile command:

```bash
gfortran -c -w pr/123947/reproducer.f90
```

Expected for affected compiler: ICE at `ALLOCATE(OBJ_BASE%OBJ(3))`.

## Notes

- Bugzilla comment #1 references `r16-5067-g9636d90e432600` as a regression
  marker.
- Bugzilla comment #3 notes the ICE was not observed under valgrind (but very
  slow), and recursive/mutual recursion in type declarations may be relevant.
- Local check on this workspace (2026-02-17):
  `gcc-offload-build/install/bin/gfortran` (`16.0.1 20260205`) compiles
  `reproducer.f90` without ICE.
