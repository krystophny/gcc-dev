# PR124512 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124512
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/104
- **Fix status:** merged
- **Regression:** yes
- **Severity:** runtime-crash
- **Validity class:** valid-code
- **Trunk commit:** f57bcde85984d2751f7bc5fd8e3de11f5dc1255
- **Trunk patch:** 0001-libgfortran-Disable-caf_shmem-without-usable-process.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |
| gcc-14 | unknown | unknown | unknown | not-run | not-run |
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `runtime-crash` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

Updated patch remains on Bugzilla as attachment 63985. A fresh full check-gfortran rerun on pr124512-fix finished clean with 0 FAIL / XPASS.
