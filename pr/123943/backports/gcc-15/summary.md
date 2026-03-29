# PR123943 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123943
- **GitHub issue:** n/a
- **Fix status:** merged
- **Regression:** yes
- **Severity:** ice-on-valid
- **Validity class:** valid-code
- **Trunk commit:** edced0fe1e28a37c75b4e2c80a2a12db93d5002c
- **Trunk patch:** 0001-fortran-Fix-DO-CONCURRENT-nested-in-block-iterator-c.patch

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-15 | unknown | unknown | unknown | not-run | not-run |

## Risk Summary

This is a `ice-on-valid` fix against `valid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.
