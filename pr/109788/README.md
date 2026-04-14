# Bug 109788: character SPREAD runtime error

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=109788
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/91

## Summary

The remaining regression was in the Fortran frontend. Character `SPREAD`
resolution specialized the shared intrinsic descriptor in place, so later
scalar uses could see the wrong call signature.

The fix copies the intrinsic descriptor before specializing the character
formal argument type and adds `gfortran.dg/pr109788.f90`.
