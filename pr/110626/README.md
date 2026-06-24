# Bug 110626: finalization sees a stale value in derived assignment

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110626
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/92

## Summary

A derived-type intrinsic assignment whose component has both a FINAL subroutine
and a defined assignment finalizes the old component value twice: once by the
whole-derived-type finalization of the lhs, once by the INTENT(OUT) argument of
the defined assignment. Both finalizations are required by the standard and ifx
and flang do the same. The bug is that gfortran's second finalization ran on a
trivial copy of the old lhs, so the final subroutine saw the stale old value
instead of the value left by the first finalization. Reference-counting code
that keys on the post-finalization state then double-frees.

## Root cause

`generate_component_assignments` (resolve.cc) rewrote the assignment as a
whole-derived-type assignment, which finalizes the lhs, plus a defined-assignment
call on a temporary copy of the old lhs. The temporary was copied bitwise but
finalized through the user-defined final subroutine, so the INTENT(OUT)
finalization saw the snapshot taken before the lhs finalization ran.

## Fix

Mark the whole-derived-type assignment as `finalize_only`: it finalizes the lhs
but does not copy the structure, and the components are assigned one by one. A
component with a defined assignment is then finalized in place by the INTENT(OUT)
argument of that assignment and sees the value left by the lhs finalization. The
two finalizations stay; only the value the second one observes changes.

This applies when the lhs type has no pointer or allocatable components, so the
structure copy is not needed for them. The allocatable-component case from
Tomáš Trnka's testcase is left for PR fortran/57696.

`reproducer.f90` checks the value the final subroutine observes on the second
finalization: the old value first, then the value the first finalization left.

## Testsuite

`finalize_46.f90` is unchanged: it already asserts the two finalizations and
keeps passing. `finalize_62.f90` is the new test; it passes on gfortran, ifx,
and flang.
