# Bug 110877: Incorrect copy of allocatable component in polymorphic assignment from array dummy argument

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110877
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/101
- **Branch:** `pr110877-fix`
- **Status:** INVESTIGATING (reproducer confirmed; current WIP fix regresses `class_transformational_1.f90`)

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

## Current WIP Fix

- Keep the existing scalarized-element hook in `gfc_trans_assignment_1`, but
  when the rhs is a class dummy array element and `rse.expr` no longer carries
  the class container, recover the vptr from the original dummy `gfc_expr`
  instead.
- Add `gfortran.dg/pr110877.f90`, a runtime regression test that checks both
  `g = f` and `allocate(g, source=f)`.

## Validation

- Direct compile and run of `reproducer.f90`: PASS
- Baseline check on clean `upstream/master`: `class_transformational_1.f90`
  PASS, original bug still reproduces (`F` then `T`)
- Current WIP compiler state: reproducer fixed (`T` then `T`)
- Blocking regression: `class_transformational_1.f90` segfaults at runtime
  after rebuilding with the WIP change
- Full `check-gfortran`: NOT RUNNABLE YET because the above regression must be
  resolved first

## Review Notes

- A broader first attempt that routed more class-array assignments through
  `_copy` fixed the bug but regressed `class_assign_4.f90` and
  `finalize_38a.f90`.
- The narrower dummy-array fallback fixes the reproducer but still introduces
  a runtime regression in `class_transformational_1.f90`, even though the
  original dump for that testcase is unchanged from baseline.
- The current WIP fix is saved locally in `gcc` stash
  `wip-pr110877-reproducer-fixed-but-class-transformational-regresses` and is
  intentionally not committed.
