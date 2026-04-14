# Bug 96986: False explicit-interface-required for ENTRY with volatile

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96986
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/71

## Summary

Calling an ENTRY with no volatile arguments incorrectly emits "Explicit
interface required: volatile argument" because the volatile attribute from a
sibling ENTRY's dummy argument is checked against the master procedure's
combined formal list.

## Root Cause

In `resolve_global_procedure`, the entry symbol lookup that replaces
`def_sym` (initially the entry master) with the specific entry symbol is
inside the `resolved != -1` block.  During recursive namespace resolution
(`resolved == -1`), the lookup is skipped and the explicit interface check
uses the master procedure's combined formals instead of the entry's own
(empty) formals.

## Fix

Move the entry symbol lookup after the `resolved != -1` block so it runs
regardless of the namespace resolution state.

Affects gcc-15, gcc-14, gcc-13 identically (same code structure).
