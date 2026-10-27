# Bug 126485: C pointer check rejects an inferred interface

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=126485
- **Attachment:** https://gcc.gnu.org/bugzilla/attachment.cgi?id=65182
- **Submission comment:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=126485#c2
- **GitHub issue:** https://github.com/lazy-fortran/gcc/issues/29
- **Fork PR:** https://github.com/lazy-fortran/gcc/pull/44
- **Branch commit:** `b8a9d0da35310a54050ba119418564ad9aba64a9`

## Summary

An implicit procedure call can acquire an inferred interface with artificial
dummy arguments. `C_LOC` has type `BT_VOID` until it is matched against a
declared dummy, so the ISO_C_BINDING check added for PR66973 rejects a later
implicit call against the inferred interface.

The test is a local two-file rewrite with different module, procedure, and
variable names. The existing PR66973 declared-interface test remains covered.
