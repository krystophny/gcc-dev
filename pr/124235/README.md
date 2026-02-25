# Bug 124235: ICE in ALLOCATE of sub-objects with recursive types

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124235
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/51
- **Status:** PENDING (patch on fork, branch `pr124235-fix`)

## Summary

GCC 16 regression: Internal compiler error when allocating a sub-object
of an already-allocated array component in a derived type that contains
recursive/self-referencing allocatable components.

Works in GCC 15, ICE in GCC 16 trunk.

## Root Cause

The deep-copy wrapper generation (PR121628) calls
`cgraph_node::add_new_function` which triggers `ggc_collect()` during
`PARSING` state.  This GC frees locally-computed COMPONENT_REF tree
nodes in caller stack frames of `structure_alloc_comps` that are not
yet attached to any GC-rooted structure.

## Fix

Replace `add_new_function` with `finalize_function(fndecl, true)` to
skip GC collection during wrapper registration.

37369 PASS, 0 FAIL on full check-gfortran.

## Reproducer

`reproducer.f90` - independently written test case with mutually-
referencing derived types and a mix of allocatable and fixed-size
array components.  ALLOCATE of parent array + sub-object triggers ICE.
