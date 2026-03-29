# PR102333 Maintainer Summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/78
- **Fix status:** open
- **Regression:** yes
- **Severity:** accepts-invalid
- **Validity class:** invalid-code
- **Trunk commit:** 8a0a1a0c7b187415e34dcf7a5cbf5e314c9de78a
- **Trunk patch:** n/a

## Active Release Branch Matrix

| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |
|--------|------------|-----------|------------|----------------|------------|
| gcc-14 | yes | yes | evidence-only | manual-matrix | not-run |

## Risk Summary

This is a `accepts-invalid` fix against `invalid-code`. Branch-specific patch data and test evidence live in `status.json` and the `backports/` subdirectories.

## Notes

Rerunning the exact Bugzilla sources on upstream branch heads on 2026-03-29 shows a split state: gcc-13 and gcc-14 still ICE on comment 0 and both comment 2 variants, gcc-15 and trunk no longer ICE, comment 1 is rejected on gcc-14/gcc-15/trunk but still accepted on gcc-13. Attachment 64064 is too broad because it rejects valid pointer cases, and Paul Thomas's suggested decl.cc line is absent from all current upstream branches.
