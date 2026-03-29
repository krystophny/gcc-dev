# PR84245 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84245
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/57
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-invalid
- **Validity class:** invalid-code
- **Trunk commit:** 486169386603627f0cf2a5f12ea4f73a20d6df20
- **Trunk patch:** 0001-fortran-Avoid-rollback-ICE-after-invalid-SELECT-TYPE.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `ice-on-invalid` fix against `invalid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

Direct reproducer no longer ICEs on clean trunk; invalid source still exits nonzero with frontend diagnostics only. Targeted testcase and repeated full check-gfortran reruns on pr84245-fix passed locally with 0 FAIL / XPASS.
