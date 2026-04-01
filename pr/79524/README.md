# Bug 79524: stale charlen after rejected parameter array declaration

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=79524
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/55
- **Branch:** `pr79524-decl-cleanup`
- **Status:** ON BUGZILLA (attachment 64114)

## Summary

`character(*), parameter :: z(2) = [character(n) :: 'x', 'y']` rejects the
declaration, but the rejection can leave declaration-local `gfc_charlen` nodes
on the namespace `cl_list`.  Later resolution revisits the stale
`character(n)` length expression and, before this fix, could walk freed symbol
state in `resolve_charlen`.

The old local patch tried to make `resolve_charlen` detect dangling symtrees.
Review on Bugzilla pushed back on that approach because it added a namespace
tree walk to resolution and kept the real problem alive longer than necessary.
The fix now cleans up the declaration-local charlens at the rejection point in
`decl.cc`, after clearing the surviving owners in that path.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only pr/79524/reproducer.f90
```

Expected result after the fix:

- user-facing diagnostic only
- no later `Scalar INTEGER expression expected` from the rejected declaration
- no Valgrind invalid read

## Local Fix

- Add `discard_pending_charlens` in `gcc/fortran/decl.cc`.
- Save the namespace `cl_list` head before matching declarations that can feed
  `add_init_expr_to_sym`.
- In the variable-length parameter-array rejection path, clear
  `sym->ts.u.cl` and `init->ts.u.cl`, then drop only the charlens created by
  that declaration after the saved list head.
- Keep the cleanup in declaration processing instead of adding a defensive
  scan in `resolve_charlen`.
- Add `gfortran.dg/pr79524.f90` to cover both `character(n)` and
  `character(n+1)` in the rejected parameter-array path.  The existing
  `fimplicit_none_2.f90` already covers the `-fimplicit-none` diagnostic path.

## Validation

- Direct compile of `reproducer.f90`: PASS
- Direct compile of two-declaration variant: PASS
- Valgrind compile of two-declaration variant: PASS
- Valgrind compile of `-fimplicit-none` reproducer: PASS
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr79524.f90"`:
  PASS
- Existing `fimplicit_none_2.f90` targeted rerun:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=fimplicit_none_2.f90"`:
  PASS
- Full `check-gfortran`:
  PASS (`0` `FAIL`/`XPASS` lines in `gcc-build/gcc/testsuite/gfortran/gfortran.sum`)
- `check-target-libgomp-fortran`:
  PASS (`0` `FAIL`/`XPASS` lines in `gcc-build/x86_64-pc-linux-gnu/libgomp/testsuite/libgomp.sum`)

## Review Notes

- The fix follows Mikael Morin's review direction from comments 20-21:
  remove the stale charlen instead of teaching `resolve_charlen` to scan for
  dangling symbols.
- The cleanup is intentionally limited to the current rejection path after
  clearing the live owners; it does not restore the old blanket
  `reject_statement` charlen rollback.

## Patch Artifact

- `pr/79524/0001-fortran-Clean-up-charlens-after-rejected-parameter-a.patch`
