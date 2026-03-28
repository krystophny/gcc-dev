# Bug 94978: bogus do-subscript warning

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=94978
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/66
- **Status:** ON BUGZILLA (attachment 64061)
- **Branch:** `origin/pr94978-fix`

## Summary

The warning was emitted from an outer-loop bound substitution even when a
nested inner loop became zero-trip for that substituted bound, making the
guarded array reference unreachable.

The fix checks nested inner loops first and suppresses the warning in that
case.

## Validation

- targeted `check-gfortran` for `pr94978.f90`
- targeted `check-gfortran` for `minmax_char_1.f90`
- targeted `check-gfortran` for `bind-c-contiguous-4.f90`
- full `check-gfortran`
- `check-target-libgomp-fortran`
