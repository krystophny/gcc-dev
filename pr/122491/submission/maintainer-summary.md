# PR122491 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122491
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/50
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-invalid
- **Validity class:** invalid-code
- **Trunk commit:** ff2f6c5153e
- **Trunk patch:** 0001-fortran-Avoid-UAF-on-missing-END-BLOCK-cleanup-PR122.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | needs-special-env | not-run | not-run |
| gcc-14 | unknown | unknown | needs-special-env | not-run | not-run |
| gcc-15 | unknown | unknown | needs-special-env | not-run | not-run |

## Risk Summary

This is a `ice-on-invalid` fix against `invalid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
