# Bug 124235: ICE in ALLOCATE of sub-objects with recursive types

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124235
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/51
- **Status:** INVESTIGATING

## Summary

GCC 16 regression: Internal compiler error when allocating a sub-object
of an already-allocated array component in a derived type that contains
recursive/self-referencing allocatable components.

Works in GCC 15, ICE in GCC 16 trunk.

## Reproducer

`reproducer.f90` - independently written test case demonstrating the
same pattern: a derived type with allocatable array components whose
element type itself has allocatable components of the same type,
followed by sequential ALLOCATE of the parent array and a sub-object.
