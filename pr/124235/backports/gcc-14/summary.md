# PR124235 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124235
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/51
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-valid
- **Validity class:** valid-code
- **Trunk commit:** e0b70284cfa
- **Trunk patch:** 0001-fortran-Fix-ICE-in-ALLOCATE-of-sub-objects-with-recu.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-14 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `ice-on-valid` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
