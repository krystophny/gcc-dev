# Bug 124512: libgfortran shmem caf: NetBSD lacks usable process-shared pthread support

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124512
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/104
- **Status:** PENDING (validated locally and on cfarm, not reposted to Bugzilla yet)

## Summary

Recent shared-memory coarray (CAF) implementation in libgfortran uses
process-shared pthread mutex and condition attributes.  On NetBSD/aarch64,
the needed APIs are not usable through the default pthread headers, so the
build fails in `libgfortran/caf/shmem/thread_support.c` unless `caf_shmem`
is disabled at configure time.

The `host_detect_local_cpu()` link failure seen during native
`aarch64-netbsd` builds has been split out into PR124586.

## Fix strategies

### Strategy now implemented
- Keep PR124512 scoped to `libgfortran` only.
- Use a real configure-time compile probe for:
  - `pthread_mutexattr_setpshared`
  - `pthread_condattr_setpshared`
  - `PTHREAD_PROCESS_SHARED`
- Disable `caf_shmem` when that probe fails.
- Remove `libcaf_shmem.la` from `cafexeclib_LTLIBRARIES` when disabled so the
  build no longer leaves behind a broken no-op target.
- Keep the probe safe for cross configuration: `AX_PTHREAD` establishes the
  baseline pthread flags, and the extra check only verifies that the
  process-shared API surface is visible through the default headers.

### Separate host-side issue
- PR124586 tracks the native `aarch64-netbsd` link failure for
  `host_detect_local_cpu()`.
- That issue is a `gcc/config.host` host-detection problem, not a
  `libgfortran` shmem CAF problem.

## Reproduction

### cfarm428.cfarm.net (NetBSD 10.1, aarch64/evbarm, 16 cores, 1TB disk)

Confirmed default-header failure on cfarm428:
```
$ cc -c /tmp/pr124512-default.c -pthread
error: 'pthread_mutexattr_setpshared' undeclared
error: 'pthread_condattr_setpshared' undeclared
```

Forcing `_PTHREAD_PSHARED` before `<pthread.h>` makes the same test compile,
matching Andre Vehreschild's observation that hidden NetBSD pthread APIs can be
forced on but do not yield a working coarray backend.

### Platform quirks discovered (2026-03-18)

1. **BSD make vs GNU make**: NetBSD default `make` is BSD make; must use `gmake`.
2. **GMP/MPFR/MPC in /usr/pkg**: Need `--with-gmp=/usr/pkg --with-mpfr=/usr/pkg --with-mpc=/usr/pkg`.
3. **libisl.so.23 in /usr/pkg/lib**: Need `LD_LIBRARY_PATH=/usr/pkg/lib` for self-tests.
4. **Separate host bug**: native `aarch64-netbsd` builds also need
   `driver-aarch64.o` linked for `host_detect_local_cpu`; that split-out
   fix is tracked in PR124586.

### Build status (2026-03-20)

- with the separate PR124586 workaround applied, a native NetBSD/aarch64 build
  reaches `libgfortran`.
- with the updated PR124512 patch, `libgfortran/configure` reports:
  `checking for usable process-shared pthread support for caf_shmem... no`
- the generated `libgfortran/Makefile` no longer tries to build
  `libcaf_shmem.la` when `ENABLE_CAF_SHMEM` is false.

## Fix

Branch `pr124512-fix` on `origin/` (krystophny/gcc fork).

### Approach: compile-only usability probe

After `AX_PTHREAD`, use an `AC_COMPILE_IFELSE` probe that includes
`<pthread.h>` and attempts to initialize pthread attribute objects and call
`pthread_mutexattr_setpshared` / `pthread_condattr_setpshared` with
`PTHREAD_PROCESS_SHARED`.

If the probe fails, disable `ENABLE_CAF_SHMEM`.

This started as an `AC_LINK_IFELSE` probe, but that is wrong after
`GCC_NO_EXECUTABLES` in cross configurations.  The final patch keeps the
same native behavior while avoiding forbidden post-`GCC_NO_EXECUTABLES`
link tests.

In addition, conditionally add `libcaf_shmem.la` to
`cafexeclib_LTLIBRARIES` only when `ENABLE_CAF_SHMEM` is true, so the build
does not try to invoke an empty `libcaf_shmem` link rule.

### Files changed

- `libgfortran/configure.ac`: add a compile-only usability probe for
  process-shared pthread support
- `libgfortran/configure`: hand-edited to match
- `libgfortran/Makefile.am`: conditionally add `libcaf_shmem.la` to
  `cafexeclib_LTLIBRARIES`
- `libgfortran/Makefile.in`: hand-edited to match

### Verification

- **Local Linux x86_64:**
  - top-level `libgfortran/config.log` reports
    `checking for usable process-shared pthread support for caf_shmem... yes`
  - standalone native `libgfortran/configure` reports the same `... yes`
  - standalone cross configure reaches the same probe with a compile test and
    does **not** trip the old
    `Link tests are not allowed after GCC_NO_EXECUTABLES` failure
  - native build produces `libgfortran`, `libcaf_single`, and `libcaf_shmem`
  - serial `gfortran.dg/coarray/caf.exp` is clean:
    - `# of expected passes 720`
    - `# of unsupported tests 6`
    - `0` FAIL / XPASS / UNRESOLVED
- **cfarm428 (NetBSD 10.1 aarch64):**
  - default-header probe fails with undeclared
    `pthread_mutexattr_setpshared` / `pthread_condattr_setpshared`
  - patched `libgfortran/configure` reports `... no`
  - clean build produces `libgfortran` and `libcaf_single`, but no
    `libcaf_shmem`
  - no `thread_support.c` compile appears in the build log

### Coarray findings

- The first cfarm coarray failures after disabling `caf_shmem` were **not**
  caused by PR124512.
- They came from `-lcaf_single` link failures against
  `__aarch64_ldadd4_relax`, `__aarch64_ldclr4_relax`,
  `__aarch64_ldset4_relax`, and `__aarch64_ldeor4_relax`.
- Those failures are the separate NetBSD/aarch64 outline-atomics problem
  tracked by PR95128.
- After layering PR95128 for testing, rebuilding `libatomic` and
  `libgfortran`, and rerunning `gfortran.dg/coarray/caf.exp` serially on
  cfarm428:
  - `# of expected passes 480`
  - `# of unsupported tests 4`
  - `0` FAIL / XPASS / UNRESOLVED

### Full tests

- A serial `check-gfortran` run on cfarm428 with PR124586 + PR124512 +
  PR95128 exposed unrelated runtime crashes in non-coarray tests such as:
  - `gfortran.dg/internal_dummy_2.f08`
  - `gfortran.dg/internal_dummy_3.f08`
  - `gfortran.dg/proc_ptr_47.f90`
  - `gfortran.dg/reduce_1.f90`
- Those failures are outside PR124512 scope.  This patch only affects whether
  `libcaf_shmem` is configured and built.
- Focused coarray reruns remain clean:
  - cfarm428: `# of expected passes 480`, `# of unsupported tests 4`
  - local Linux: `# of expected passes 720`, `# of unsupported tests 6`

## Key participants

- **Andre Vehreschild** (vehre@gcc.gnu.org): Assignee-equivalent, author of shmem CAF.
- **Patrick Welche**: Reporter, NetBSD maintainer, providing build details.
- **Richard Biener**: Marked P1, suggested configure-based solutions.
