# Bug 125383: optional dummy procedure loses host association

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=125383
- **Attachment:** https://gcc.gnu.org/bugzilla/attachment.cgi?id=65180
- **Submission comment:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=125383#c11
- **GitHub issue:** https://github.com/lazy-fortran/gcc/issues/24
- **Fork PR:** https://github.com/lazy-fortran/gcc/pull/41
- **Branch commit:** `b49e94c6a9589a7eef39b0291575c5054cc41649`

## Summary

A call marks an unresolved procedure as a subroutine before its procedure kind
is known. `was_declared` treated that provisional attribute as a declaration,
so resolution missed the optional dummy procedure in the host scope and
generated a reference to a nonexistent external symbol.

The test is a local rewrite with different module, procedure, and variable
names. It checks both absent and present optional callbacks.
