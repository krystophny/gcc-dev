# Bug 124631: [UBSAN] simplify.cc:3088:12 runtime error

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124631
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/111

## Summary

The rank-1 `gfc_simplify_eoshift` path initialized `extent[0]` and `count[0]`
but left `sstride[0]` uninitialized. Folded `EOSHIFT` shape/kind inquiries could
then read the stale stride entry and trigger the UBSAN report from PR124631.

## Fix

- Upstream commit: `73933cdc44dea4b1bd5e1a2ef04d1df6edeb27c6`
- Upstream revision: `r16-8308-g73933cdc44dea4b1bd5e1a2ef04d1df6edeb27c6`
- Local validation branch: `pr124631-fix`
- Local validation commit: `29b21a5605f`
- Local patch: `0001-fortran-Initialize-rank-1-EOSHIFT-stride-PR124631.patch`

Initialize `sstride[0]` to zero before entering the rank-1 simplification path.
The local patch was completed before the live Bugzilla rescan; Harald Anlauf's
upstream commit landed first and superseded local posting.
