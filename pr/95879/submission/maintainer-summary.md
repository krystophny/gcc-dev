# PR95879 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95879
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/69
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-valid
- **Validity class:** valid-code
- **Trunk commit:** ee931e5b7eab59916f4dd77a4ad20c1202153036
- **Trunk patch:** 0001-fortran-Fix-use-after-free-in-gfc_fixup_sibling_symb.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-13 | unknown | unknown | unknown | not-run | not-run |
| gcc-14 | unknown | unknown | unknown | not-run | not-run |
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `ice-on-valid` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

Merged upstream as r16-8320-gee931e5b7eab59916f4dd77a4ad20c1202153036 (commit ee931e5b7eab59916f4dd77a4ad20c1202153036). A fresh full check-gfortran rerun on pr95879-fix finished clean with 0 FAIL / XPASS. Paul Thomas noted that backports should wait a couple of weeks.
