# Bug 109788: character SPREAD runtime error

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=109788
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/91
- **Status:** ON BUGZILLA (attachment 64059)
- **Branch:** `origin/pr109788-fix`

## Summary

The remaining regression was in the Fortran frontend. Character `SPREAD`
resolution specialized the shared intrinsic descriptor in place, so later
scalar uses could see the wrong call signature.

The fix copies the intrinsic descriptor before specializing the character
formal argument type and adds `gfortran.dg/pr109788.f90`.

## Validation

- targeted `check-gfortran` for `pr109788.f90`
- targeted `check-gfortran` for `spread_scalar_source.f90`
- targeted `check-gfortran` for `intrinsic_spread_1.f90`
- targeted `check-gfortran` for `intrinsic_spread_2.f90`
- full `check-gfortran`
- `check-target-libgomp-fortran`
