# Bug 94978: bogus do-subscript warning

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=94978
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/66

## Summary

The warning was emitted from an outer-loop bound substitution even when a
nested inner loop became zero-trip for that substituted bound, making the
guarded array reference unreachable.

The fix checks nested inner loops first and suppresses the warning in that
case.
