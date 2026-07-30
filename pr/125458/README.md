# Bug 125458: constant overflow diagnostic is discarded

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=125458
- **Attachment:** https://gcc.gnu.org/bugzilla/attachment.cgi?id=65181
- **Submission comment:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=125458#c18
- **GitHub issue:** https://github.com/lazy-fortran/gcc/issues/27
- **Fork PR:** https://github.com/lazy-fortran/gcc/pull/43
- **Branch commit:** `6a83c59d69d931703b6b1b47d374a70f4541e09d`

## Summary

`eval_intrinsic` keeps an out-of-range result for error recovery but buffers
the overflow diagnostic. A successful statement match can discard the
diagnostic while retaining the invalid constant.

The patch emits range-checked overflow immediately outside unsigned mode. The
test uses independently chosen integer expressions rather than the reporter's
values.
