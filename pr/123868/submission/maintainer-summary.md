# PR123868 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123868
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/47
- **Fix status:** merged
- **Regression:** yes
- **Severity:** wrong-code
- **Validity class:** valid-code
- **Trunk commit:** ca448bc5e435
- **Trunk patch:** 0001-fortran-Fix-memory-leak-on-assignment-with-nested-al.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |
| gcc-14 | unknown | unknown | unknown | not-run | not-run |
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `wrong-code` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
