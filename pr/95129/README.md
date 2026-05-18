# Bug 95129: aarch64 outline atomics on non-GNU targets

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95129
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/105
- **Related:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95128

## Summary

On aarch64, outline atomics use `__getauxval` for runtime LSE detection.
That path is Linux-specific. Non-GNU targets need either target-specific
runtime detection or a default that avoids unresolved outline-atomic helper
symbols.

The local PR95128 patch takes the narrow NetBSD path: disable outline
atomics by default for aarch64 NetBSD while preserving explicit
`-moutline-atomics`. PR95129 tracks the broader runtime-detection problem.
