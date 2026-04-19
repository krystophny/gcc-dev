# Bug 42954: Target CPP builtins missing in gfortran -cpp

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=42954
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/52
- **Status:** PENDING USER REVIEW (v4 patch built, tested, and committed on pr42954-fix branch; not yet pushed; not yet posted to Bugzilla)

## Summary

Replaces the v2/v3 code-duplication approach with a shared implementation.
Pure x86 preprocessor macro emission moves from `gcc/config/i386/i386-c.cc`
into a new `gcc/config/i386/i386-cppbuiltin.cc` that is linked into cc1,
cc1plus, and f951 (via c_target_objs, cxx_target_objs, and
fortran_target_objs in `gcc/config.gcc`, matching the existing darwin-f.o
and vms-f.o precedent).  A new `TARGET_GENERIC_CPU_CPP_BUILTINS` hook is
the language-neutral sibling of `TARGET_CPU_CPP_BUILTINS`; Fortran invokes
it via a single `#ifdef`, so `gcc/fortran/cpp.cc` no longer contains any
x86-specific code.

The old Fortran-only shims (`gfc_builtin_define_std` /
`gfc_builtin_define_with_value`) remain as the glue between Linux/Darwin/
ELF target config headers and the Fortran frontend, enabling
`TARGET_OS_CPP_BUILTINS` and `TARGET_OBJFMT_CPP_BUILTINS`.

## Patch history

| Version | Attachment | Approach |
|---------|-----------|----------|
| v1 | 64224 (obsoleted) | Fortran-only shims; flag_iso=0; caused bare-name pollution |
| v2 | 64225           | Fortran-only shims; flag_iso=1; still duplicated x86 code |
| v3 (unposted)      | Same as v2 plus ISA feature macros duplicated again in fortran/cpp.cc |
| v4 (this tree)     | Deduplication: shared file i386-cppbuiltin.{cc,h} + TARGET_GENERIC_CPU_CPP_BUILTINS hook |

## Validation (v4)

| Suite                          | Result |
|--------------------------------|--------|
| `check-gfortran`               | only bessel_6 failures (PR124819, acknowledged pre-existing) |
| `check-target-libgomp-fortran` | 0 FAIL, 0 XPASS; both libgomp.fortran/fortran.exp and libgomp.oacc-fortran/fortran.exp ran |
| `check-gcc` (first run)        | 99 FAIL / 23 XPASS, of which 118 are known-flaky `guality/` and `asan/` categories; 4 real failures (`gcc.target/i386/pr115102`, `pr122021-0`, `xchg-4` x2) are explained by this build's `--disable-multilib` (no 32-bit libgcc) and `-Og` debug-build codegen; none touch files this patch modifies |
| `check-c++`                    | Not run: this build tree is `--enable-languages=c,fortran,lto` only, no cc1plus |

Byte-identical target-macro output between `gcc -E -dM -x c` and
`gfortran -cpp -E -dM` confirmed across 14 scenarios by `/tmp/pr42954-verify.sh`,
including `-march=haswell`, `-march=skylake-avx512`, `-march=znver5 -mavx512f`,
`-march=native`, `-mcmodel=large`, `-mcmodel=kernel`, `-m32`, `-m32 -march=i686`,
`-mno-sse -mno-sse2 -mno-80387`, `-march=haswell -mcmodel=medium -fcf-protection=full`,
and others.

## Affected Versions

| Branch | Reproduces? | Notes |
|--------|-------------|-------|
| trunk (r16-xxxx) | yes | never worked; architectural gap since 2008 |

Not a regression.  Target: stage 1.
