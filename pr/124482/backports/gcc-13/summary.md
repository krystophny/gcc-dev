# PR124482 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124482
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/102
- **Fix status:** merged
- **Regression:** yes
- **Severity:** runtime-crash
- **Validity class:** valid-code
- **Trunk commit:** d8b00bf2e1514cd132a9febaa9849ab46cd316f5
- **Trunk patch:** 0001-fortran-Fix-use-after-free-in-CLASS-component-error-.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `runtime-crash` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
