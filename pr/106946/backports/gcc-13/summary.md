# PR106946 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=106946
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/88
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-invalid
- **Validity class:** invalid-code
- **Trunk commit:** n/a
- **Trunk patch:** 0001-fortran-Fix-ICE-on-invalid-CLASS-component-in-derive.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | no | no | not-affected | not-run | not-run |

## Risk Summary

This is a `ice-on-invalid` fix against `invalid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
