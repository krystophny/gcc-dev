# Bug 110626: duplicated finalization in derived assignment

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110626
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/92

## Summary

Assignment of a derived type containing a finalizable component can finalize
the component twice when defined assignment is involved. Bugzilla tracks this
as a wrong-code regression from GCC 13 onward.

Paul Thomas is assigned upstream. The last local issue state recorded this as
a high-complexity finalization and defined-assignment interaction with no
posted patch.
