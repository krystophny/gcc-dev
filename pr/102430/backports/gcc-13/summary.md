# PR102430 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102430
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/9
- **Fix status:** patch-ready
- **Regression:** yes
- **Severity:** ice-on-valid
- **Validity class:** valid-code
- **Trunk commit:** d498fe6e019
- **Trunk patch:** 0001-fortran-Reject-array-allocatable-LINEAR-on-DO-PR1024.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | yes | yes | validated-targeted | pass | not-run |

## Risk Summary

This is a `ice-on-valid` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
