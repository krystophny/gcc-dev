# PR109788 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=109788
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/91
- **Fix status:** patch-ready
- **Regression:** yes
- **Severity:** runtime-crash
- **Validity class:** valid-code
- **Trunk commit:** n/a
- **Trunk patch:** 0001-fortran-Fix-character-SPREAD-intrinsic-lowering-PR10.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `runtime-crash` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
