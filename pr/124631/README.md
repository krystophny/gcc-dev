# Bug 124631: [UBSAN] simplify.cc:3088:12 runtime error

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124631
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/111
- **Status:** PENDING (patch on fork; not yet posted to Bugzilla)

## Summary

The rank-1 `gfc_simplify_eoshift` path initialized `extent[0]` and `count[0]`
but left `sstride[0]` uninitialized. Folded `EOSHIFT` shape/kind inquiries could
then read the stale stride entry and trigger the UBSAN report from PR124631.

## Fix

- Branch: `pr124631-fix`
- Commit: `29b21a5605f`
- Patch: `0001-fortran-Initialize-rank-1-EOSHIFT-stride-PR124631.patch`

Initialize `sstride[0]` to zero before entering the rank-1 simplification path.

## Verification

- Reproducer `/tmp/pr124631.f90` now runs clean.
- `make check-gfortran RUNTESTFLAGS='dg.exp=pr124631.f90'`
- Full `check-gfortran`: `0` `FAIL` / `XPASS`, `# of expected passes 3425`

