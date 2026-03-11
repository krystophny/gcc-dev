# PR123949 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123949
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/49
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-valid
- **Validity class:** valid-code
- **Trunk commit:** 05159b27621
- **Trunk patch:** 0001-fortran-Initialize-gfc_se-in-PDT-component-allocatio.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | no | no | not-affected | not-run | not-run |

## Risk Summary

This is a `ice-on-valid` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
