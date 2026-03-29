# PR108382 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=108382
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/110
- **Fix status:** patch-ready
- **Regression:** yes
- **Severity:** wrong-code
- **Validity class:** valid-code
- **Trunk commit:** f738265ceff7bc2fa3ebcbaf0dc7d807e81d81a8
- **Trunk patch:** 0001-fortran-Fix-free-form-mixed-OpenACC-OpenMP-continuat.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |
| gcc-14 | unknown | unknown | unknown | not-run | not-run |
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `wrong-code` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

Patch posted to Bugzilla as attachment 63999. Validation on pr108382-fix is now complete: original and reduced reproducers fixed, preserved negative case still diagnoses, goacc.exp=omp-108382.f90 passes, goacc.exp=omp.f95 passes, the broader goacc.exp sweep is clean, and a fresh full check-gfortran rerun finished with 0 FAIL / XPASS.
