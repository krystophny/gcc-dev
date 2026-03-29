# PR120723 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120723
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/96
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-valid
- **Validity class:** valid-code
- **Trunk commit:** 0af9613810ecdc991633f58f5dd81a574aa2af31
- **Trunk patch:** 0001-fortran-Fix-scalar-OpenACC-attach-detach-lowering-PR.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-14 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `ice-on-valid` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
