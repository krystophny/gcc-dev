# Bug 93814: ICE in build_entry_thunks with CHARACTER bind(c) ENTRY

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93814
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/64

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
