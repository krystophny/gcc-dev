# Bug 110877: Incorrect copy of allocatable component in polymorphic assignment from array dummy argument

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110877
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/101

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
