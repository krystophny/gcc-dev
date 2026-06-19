# Bug 110626: duplicated finalization in derived assignment

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110626
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/92

## Summary

Assigning a derived type whose component has both a FINAL subroutine and a
defined assignment finalized the old component value twice. The assignment ran
once, so reference-counting code that frees a resource in the finalizer saw a
double free.

## Root cause

`generate_component_assignments` (resolve.cc) rewrites the assignment two ways
at once. It marks the whole-derived-type intrinsic assignment of the lhs for
finalization, which emits `__final_<type>` over every component. For a
component with a defined assignment it also builds a temporary holding the old
lhs and calls the defined assignment with an INTENT(OUT) first argument, which
finalizes that old value again. Both finalizations hit the same old component
value.

The whole-struct finalization came in with the PR37336 finalization rework
(r13, March 2023), which is why the double finalization is a GCC 13 regression.

## Fix

Count the finalizable components and the ones finalized by their own
INTENT(OUT) defined assignment. When the lhs type has no FINAL of its own and
every finalizable component is finalized by such a defined assignment, the
whole-struct finalization only repeats those calls, so it is dropped. Mixed
types and types with their own FINAL keep the existing behavior.

`reproducer.f90` compares a direct assignment of the finalizable type against
the same type assigned as a component; the finalization counts must match.

## Testsuite

`finalize_46.f90` asserted the old double count while its comments described a
single finalization per assignment; the patch aligns the counts with the
comments. `finalize_62.f90` is the new direct-versus-component check.
