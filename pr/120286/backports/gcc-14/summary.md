# PR120286 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120286
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/95
- **Fix status:** merged
- **Regression:** yes
- **Severity:** runtime-crash
- **Validity class:** valid-code
- **Trunk commit:** n/a
- **Trunk patch:** 0001-fortran-Preserve-scalar-class-pointers-in-OpenMP-pri.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-14 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `runtime-crash` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

2026-03-17: moved the OpenMP runtime testcase to libgomp/testsuite/libgomp.fortran after review feedback from Tobias Burnus; reran full check-fortran with 0 FAIL/XPASS in the aggregated gfortran and libgomp sums. Merged upstream as r16-8123-g60fbabc1a182cc (commit 60fbabc1a182cca77d14c68a1b623c554310d135).
