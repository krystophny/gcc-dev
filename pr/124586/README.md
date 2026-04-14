# Bug 124586: aarch64-netbsd native build misses driver-aarch64.o for host_detect_local_cpu

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124586
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/109

## Summary

Native `aarch64-netbsd` builds fail during stage1 link because
`gcc/config.host` does not include `aarch64*-*-netbsd*` in the host pattern
that selects `driver-aarch64.o`.  The driver then links without
`host_detect_local_cpu`, producing an undefined reference.

This issue was discovered while testing PR124512 on cfarm428, but Andre
Vehreschild confirmed on 2026-03-20 that it is separate from the
`libgfortran` shmem CAF build failure.

## Reproduction

### cfarm428.cfarm.net (NetBSD 10.1, aarch64/evbarm)

Native trunk build fails while linking the driver:

```text
undefined reference to `host_detect_local_cpu'
```

Root cause in `gcc/config.host`:

```text
aarch64*-*-freebsd* | aarch64*-*-linux* | aarch64*-*-fuchsia* | \
aarch64*-*-darwin*)
```

`aarch64*-*-netbsd*` is missing even though the same logic already exists for
other native AArch64 hosts, and `arm*-*-netbsd*` is already handled
separately.

## Fix

Add `aarch64*-*-netbsd*` to the host pattern so native NetBSD/AArch64 builds
set:

```text
host_extra_gcc_objs="driver-aarch64.o"
```

## Notes

- Related discovery thread: PR124512 comment trail on 2026-03-20.
- Older analogue: PR77800 covered `netbsd/arm`; this is the `aarch64` case.
- Host-side support alone is not sufficient for native NetBSD/aarch64 builds:
  once this fix is applied, the build proceeds to `libgfortran` and then hits
  PR124512 in `libgfortran/caf/shmem/thread_support.c`.
