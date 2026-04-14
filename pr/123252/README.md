# PR123252 - OpenACC: derived-type scalar reads wrong on device

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123252
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/11

- **Bugzilla status:** UNCONFIRMED

kernel when only array component is mapped

**Component:** fortran (OpenACC)

## Summary

When an OpenACC enter data maps only an allocatable component of a Fortran
derived type (for example `enter data copyin(c%arr(...))`), gimplify still
creates a `GOMP_MAP_STRUCT` mapping for the enclosing derived object.  Before
this change, that struct mapping did not also copy scalar, non-pointer
components such as `c%flag` or `c%n`, so later device kernels could read those
scalar fields as garbage and take the wrong branch.

The reproducer is `reproducer.f90`.  It prints `PASS` when `c%flag` is observed
as true on the device and prints `FAIL` and exits non-zero otherwise.
