# PR124661 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124661
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/112
- **Fix status:** patch-ready
- **Regression:** yes
- **Severity:** runtime-crash
- **Validity class:** valid-code
- **Trunk commit:** 96e43eec01c
- **Trunk patch:** 0001-fortran-Fix-descriptor-factoring-for-bounds-checked-.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `runtime-crash` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

Patch posted to Bugzilla as attachment 64058. Reproducer now runs clean with -fcheck=bounds. Targeted pr124661.f90 and assign_14.f90 tests pass, and a full check-gfortran rerun on pr124661-fix4 finished with 0 FAIL / XPASS.
