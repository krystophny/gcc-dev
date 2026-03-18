# Bug 124512: libgfortran shmem caf: NetBSD has no pthread_condattr_setpshared

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124512
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/104
- **Status:** INVESTIGATING (P1, Andre Vehreschild actively working)

## Summary

Recent shared-memory coarray (CAF) implementation in libgfortran uses
`pthread_condattr_setpshared()` and `pthread_mutexattr_setpshared()`,
which NetBSD does not support. Build failure on NetBSD targets.

Additionally, an undefined reference to `host_detect_local_cpu()` was
reported during stage1 build on aarch64-netbsd10.1, though this may be
a separate aarch64-specific issue.

## Fix strategies

### Strategy 1: Configure-time detection (suggested by reporter)
- Use `AC_CHECK_FUNCS` to detect `pthread_condattr_setpshared` availability.
- Guard the shmem CAF implementation with `#ifdef HAVE_PTHREAD_CONDATTR_SETPSHARED`.
- Fallback to disabling shmem CAF on platforms without support.

### Strategy 2: Configure option (suggested by richi)
- Add `--disable-shmem-caf` configure flag.
- Or use target blacklisting to exclude known-unsupported platforms.

### Strategy 3: Alternative synchronization primitives
- Replace `pthread_*attr_setpshared` with platform-portable alternatives.
- E.g., use `sem_init(pshared=1)` or file-based locks as fallback.
- More complex but provides broader platform support.

### aarch64-netbsd issue
- Undefined reference to `host_detect_local_cpu()` in `driver-aarch64.cc`.
- Likely a build system issue (missing object linkage), not directly related
  to the pthread problem.
- May be a parallel build race condition or missing dependency.

## Reproduction

### cfarm428.cfarm.net (NetBSD 10.1, aarch64/evbarm, 16 cores, 1TB disk)

Confirmed `pthread_condattr_setpshared` is missing:
```
$ cc -o /tmp/test_pshared /tmp/test_pshared.c -lpthread
warning: implicit declaration of function 'pthread_condattr_setpshared'
ld: undefined reference to `pthread_condattr_setpshared'
```

Build script: `cfarm428-build.sh` (run via `ssh cfarm428.cfarm.net 'bash -s' < pr/124512/cfarm428-build.sh`)

```bash
# One-time setup
ssh cfarm428.cfarm.net
mkdir -p ~/gcc-dev && cd ~/gcc-dev
git clone --depth 1 git://gcc.gnu.org/git/gcc.git

# Build (handles all workarounds)
bash -s < pr/124512/cfarm428-build.sh
```

### Platform quirks discovered (2026-03-18)

1. **BSD make vs GNU make**: NetBSD default `make` is BSD make; must use `gmake`.
2. **GMP/MPFR/MPC in /usr/pkg**: Need `--with-gmp=/usr/pkg --with-mpfr=/usr/pkg --with-mpc=/usr/pkg`.
3. **libisl.so.23 in /usr/pkg/lib**: Need `LD_LIBRARY_PATH=/usr/pkg/lib` for self-tests.
4. **config.host missing NetBSD for aarch64**: `host_detect_local_cpu` not linked.
   Pattern `aarch64*-*-freebsd* | aarch64*-*-linux* | aarch64*-*-fuchsia* | aarch64*-*-darwin*`
   does not include `aarch64*-*-netbsd*`. This is a **separate bug** from PR124512.
   Workaround: patch line 103 of `gcc/config.host` to add `aarch64*-*-netbsd*`.

### Build status

- config.host patch applied, compiler (f951/gfortran) builds successfully.
- Waiting for libgfortran build to hit the pthread_condattr_setpshared failure.

## Key participants

- **Andre Vehreschild** (vehre@gcc.gnu.org): Assignee-equivalent, author of shmem CAF.
- **Patrick Welche**: Reporter, NetBSD maintainer, providing build details.
- **Richard Biener**: Marked P1, suggested configure-based solutions.
