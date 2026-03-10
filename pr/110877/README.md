# Bug 110877: Incorrect copy of allocatable component in polymorphic assignment from array dummy argument

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110877
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/101
- **Branch:** `pr110877-fix`
- **Status:** PATCH READY (signed patch on fork)

## Summary

`class` array assignment from a polymorphic array dummy argument currently
falls through the generic scalarized assignment path.  That path copies each
element by raw struct assignment, so allocatable components in the dynamic
type are not deep-copied.  In the reproducer, `g = f` leaves `g(1)%a`
unallocated even though `allocate(g, source=f)` preserves it correctly.

The tree dump shows the split directly: `SOURCE=` lowers through
`g._vptr->_copy (...)`, while ordinary assignment from the dummy array emits a
plain element assignment on the underlying `struct foo_t`.

## Reproducer

`reproducer.f90`

Compile and run:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc pr/110877/reproducer.f90 -o /tmp/pr110877
/tmp/pr110877
```

Expected result after the fix:

- `g = f` preserves allocation status of `bar_t%a`
- `allocate(g, source=f)` still preserves allocation status

## Fix

- Keep the existing scalarized-element hook in `gfc_trans_assignment_1`, but
  extend it only for nonpointer, nonallocatable class dummy arrays.
- When scalarization has reduced `rse.expr` to the data object and the class
  container is no longer present there, recover the vptr from the original
  dummy `gfc_expr` via `gfc_get_class_from_gfc_expr (expr2)`.
- Reuse the existing `_copy` machinery once the vptr has been recovered.
- Add `gfortran.dg/pr110877.f90`, a runtime regression test that checks both
  `g = f` and `allocate(g, source=f)`.

## Validation

- Direct compile and run of `reproducer.f90`: PASS
- Direct runtime check of the fixed compiler: reproducer now prints `T` then `T`
- Direct runtime rechecks:
  - `class_transformational_1.f90`: PASS
  - `class_assign_4.f90`: PASS
  - `finalize_59.f90`: PASS
  - `class_dummy_6.f90`: PASS
  - `pr99326.f90` (`-fsyntax-only`): PASS
- Targeted `check-gfortran`:
  - `pr110877.f90`: PASS
  - `class_transformational_1.f90`: PASS
  - `class_assign_4.f90`: PASS
  - `finalize_59.f90`: PASS
  - `class_dummy_6.f90`: PASS
  - `pr99326.f90`: PASS
- Full `check-gfortran`: PASS (`0` `FAIL`/`XPASS`)

## Review Notes

- A broader first attempt that routed more class-array assignments through
  `_copy` fixed the bug but regressed `class_assign_4.f90` and
  `finalize_38a.f90`.
- A later dummy-variable-only attempt also regressed `finalize_59.f90` by
  sending class pointer results through `_copy`.
- The accepted fix is narrower: only scalarized elements of nonpointer,
  nonallocatable class dummy arrays use the recovered-vptr path.
- `finalize_38a.f90` was rechecked against a temporarily restored baseline and
  already fails there, so it is not caused by this patch.

## Patch Artifacts

- GCC commit: `55493d38c019728320a728481b0f010dddf861fc`
- Exported patch:
  `pr/110877/0001-fortran-Fix-class-dummy-array-assignment-deep-copy-P.patch`
- Branch: `origin/pr110877-fix`
