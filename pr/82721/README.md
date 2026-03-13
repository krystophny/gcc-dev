# Bug 82721: Corrupted error message / ICE after duplicate type

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82721
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/56
- **Branch:** `pr82721-fix`
- **Status:** MERGED (r16-8023-g5cfaad50af7dc)

## Summary

`CHARACTER(len(...))` declarations allocate `gfc_charlen` nodes on the current
namespace while parsing the type-spec.  If the declaration is later rejected
because the symbol was already declared with a different type, those fresh
charlen nodes survive statement rollback.  Resolution later walks the stale
`len(c)` expression and can produce corrupted diagnostics or segfault.

## Reproducer

`reproducer.f90`

Compile command:

```bash
MALLOC_PERTURB_=165 gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only \
  pr/82721/reproducer.f90
```

Expected result after the fix:

- diagnostic about the duplicate declaration
- no internal compiler error

## Local Fix

- In `build_sym`, when `gfc_add_type` rejects a duplicate declaration, drop the
  fresh unattached `gfc_charlen` node that was created for that symbol before
  it ever reached `sym->ts.u.cl`.
- Only discard charlen nodes that are not shared with an already-accepted
  declaration, so existing invalid-code diagnostics in `charlen_*.f90` keep the
  state they rely on.
- Clear `current_ts` when the rejected declaration was still using the original
  typespec charlen node.
- Add `gfortran.dg/pr82721.f90`, using `dg-set-target-env-var MALLOC_PERTURB_`
  to make the old failure deterministic.

## Validation

- Direct perturbed compile of `reproducer.f90`: PASS (diagnostic only, no ICE)
- Direct perturbed compile of minimal variant: PASS (diagnostic only, no ICE)
- 20 repeated perturbed compiles of the minimal variant: PASS
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr82721.f90"`:
  PASS
- Full `check-gfortran`:
  PASS (`0` `FAIL`/`XPASS` lines in `gcc-build/gcc/testsuite/gfortran/gfortran.sum`)

## Patch Artifact

- `pr/82721/0001-fortran-Fix-ICE-after-rejected-CHARACTER-duplicate-d.patch`
