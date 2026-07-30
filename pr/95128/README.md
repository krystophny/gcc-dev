# Bug 95128: aarch64: configure option for outline-atomics

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95128
- **Attachment:** https://gcc.gnu.org/bugzilla/attachment.cgi?id=65183
- **Submission comment:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95128#c5
- **GitHub issue:** https://github.com/lazy-fortran/gcc/issues/10
- **Fork PR:** https://github.com/lazy-fortran/gcc/pull/35
- **Branch commit:** `5cb3c70f5bf884d6dc83526ab3f38895b252a0a1`

- **See also:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95129

## Summary

On aarch64, outline-atomics are enabled by default (`Init(2)` in `aarch64.opt`).
The runtime LSE detection (`lse-init.c`) only works on GNU/Linux via `__getauxval`.
NetBSD's `libgcc/config.host` does not include `t-lse`, so the out-of-line atomic
helper functions are never built, causing link failures.

## Root cause

1. Compiler emits calls to `__aarch64_ldadd4_relax` etc. (outline atomics)
2. `libgcc` on NetBSD does not build `lse.S` (no `t-lse` in config.host)
3. Link fails with undefined references

## Fix

Add `-mno-outline-atomics` as default in `CC1_SPEC` in `aarch64-netbsd.h`.
User can still override with explicit `-moutline-atomics`.

## Files changed

- `gcc/config/aarch64/aarch64-netbsd.h`: add `-mno-outline-atomics` to CC1_SPEC

## Test results

- Linux x86_64 (local): build succeeds, no effect (x86_64 target)
- aarch64--netbsd cross cc1: default and explicit override checks pass
