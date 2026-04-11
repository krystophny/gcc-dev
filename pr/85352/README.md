# Bug 85352: valid ENTRY specification expressions rejected

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85352
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/59
- **Status:** MERGED (r16-8499-gbd0134b0289687)
- **Upstream commit:** `bd0134b02896878319cbfd0c4128df49f8790019`
- **Branch:** `origin/pr85352-fix`

## Summary

The bad reject-valid diagnostic came from losing the context of which dummy's
specification expressions were currently being resolved.

The fix tracks that dummy and suppresses the before-the-`ENTRY` diagnostic only
for sibling `ENTRY` arguments in the same still-unresolved `ENTRY`.

## Validation

- targeted `check-gfortran` for `pr85352.f90`
- full `check-gfortran`
- `check-target-libgomp-fortran`
