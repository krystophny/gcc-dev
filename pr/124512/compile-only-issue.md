# Superseded by PR124586

The host-side compile-enablement hunk that adds `aarch64*-*-netbsd*` to
`gcc/config.host` was split out of PR124512 after the 2026-03-20 Bugzilla
discussion.

Current home:

- Bugzilla: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124586
- GitHub issue: https://github.com/krystophny/gcc-dev/issues/109
- Local tracking: `pr/124586/`

PR124512 now tracks only the `libgfortran` configure-side shmem CAF fix.
