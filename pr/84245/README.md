# Bug 84245: ICE in `delete_root` during invalid `SELECT TYPE`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84245
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/57
- **Status:** ON BUGZILLA (attachment 63998; full trunk validation complete)

## Summary

Invalid `SELECT TYPE` statements can ICE in parser rollback when expression
matching fails after the temporary block namespace has already been created.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-trunk-build/gcc/gfortran -B gcc-trunk-build/gcc -c pr/84245/reproducer.f90 -o /dev/null
```

Expected result after the fix:

- front-end diagnostics only
- no internal compiler error
- nonzero exit status is expected because the source is invalid

## Patch

- GCC branch: `pr84245-fix`
- GCC commit: `e0115b2d28e1a030c6158f2c57a2ebfd62507d1b`
- Exported patch: `0001-fortran-Avoid-rollback-ICE-after-invalid-SELECT-TYPE.patch`

## Fix approach

- In `gfc_match_select_type`, distinguish `MATCH_NO` from `MATCH_ERROR`.
- Only free the temporary namespace on `MATCH_NO`.
- On `MATCH_ERROR`, return immediately and avoid running the normal rollback
  path over a partially broken namespace.

## Validation

- direct reproducer: fixed, no ICE, diagnostics only
- targeted tests: `dg.exp=pr84245.f90` passed
- full `check-gfortran`: passed with no `FAIL`/`XPASS` entries

## Notes

- This is in the same general parser/error-recovery family as PR106946 and
  PR82721, but the failing path is in `gfc_match_select_type`.
- Bugzilla already has a candidate patch with the same basic control-flow fix.
