# Bug 93814: ICE in build_entry_thunks with CHARACTER bind(c) ENTRY

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93814
- **Status:** PENDING (patch on fork, branch pr93814-fix)

## Summary

A CHARACTER function with `bind(c)` and a CHARACTER ENTRY with `bind(c)`
triggers an ICE (segfault) in `build_entry_thunks` at trans-decl.cc.

## Root Cause

The entry master function returns CHARACTER by reference (void return type,
result passed as pointer + length arguments). Individual bind(c) entry
thunks return CHARACTER(1) by value and have no result-reference arguments.
`build_entry_thunks` unconditionally forwarded the result-reference
arguments from the thunk's parameter list, accessing `DECL_ARGUMENTS` of
a function that has no arguments.

## Fix

When the master returns by reference but the thunk does not (bind(c)
CHARACTER), create local temporaries for the result buffer and character
length in the thunk. Pass these to the master call, then load the
character value from the buffer and return it by value.

## Release Branch Applicability

The bug was introduced by r9-5391-g264201216816c914 (GCC 9). The fix
applies to all active release branches (gcc-15, gcc-14, gcc-13) since
`build_entry_thunks` has not changed materially in this area.
