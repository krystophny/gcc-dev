# PR124208 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124208
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/100
- **Fix status:** merged
- **Regression:** yes
- **Severity:** wrong-code
- **Validity class:** valid-code
- **Trunk commit:** 97965bdc1ed
- **Trunk patch:** 0001-fortran-Fix-iterator-counting-in-nested-block-scopes.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |
| gcc-14 | unknown | unknown | unknown | not-run | not-run |
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `wrong-code` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
