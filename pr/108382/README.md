# Bug 108382: mixed OpenACC/OpenMP continuation misparse

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=108382
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/110
- **Status:** MERGED (r16-8329-g3d4039e95d851b)
- **Upstream commit:** `3d4039e95d851b5e3d8241b1feaf1d5dcc00cb98`

## Summary

With both `-fopenmp` and `-fopenacc` enabled, a continued free-form
OpenACC directive can leave the OpenACC continuation state live across the
next independent OpenMP directive, and vice versa. The next continued line is
then misparsed as a mixed continuation, leading to bogus diagnostics such as:

- `Wrong OpenACC continuation ... expected !$ACC, got !$OMP`
- `Wrong OpenMP continuation ... expected !$OMP, got !$ACC`

This rejects valid code.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-trunk-build/gcc/gfortran -B gcc-trunk-build/gcc -c -fopenmp -fopenacc \
  pr/108382/reproducer.f90 -o /dev/null
```

## Current local fix

- The bug is in the free-form scanner, not in later OpenMP/OpenACC parsing.
- `skip_free_omp_sentinel` and `skip_free_oacc_sentinel` were leaving the
  opposite directive flag live when a new directive line started with normal
  directive whitespace rather than being a continuation line.
- The fix clears the opposite flag only for those non-continuation free-form
  directive starts, matching the fixed-form behavior already added in
  `4facf2bf5b7`.

## Notes

- Current trunk still reproduces the free-form bug with both the original
  `declare` example and a smaller `enter data` / `flush release` reduction.
- The fixed-form variant from the Bugzilla comment does not reproduce in the
  current local build, so the local fix is intentionally limited to the
  free-form scanner path for now.

## Patch

- Branch: `pr108382-fix`
- Commit: `f738265ceff7bc2fa3ebcbaf0dc7d807e81d81a8`
- Upstream commit: `3d4039e95d851b5e3d8241b1feaf1d5dcc00cb98`
- Patch: `0001-fortran-Fix-free-form-mixed-OpenACC-OpenMP-continuat.patch`

## Validation

- Original Bugzilla reproducer now compiles cleanly with
  `-fopenmp -fopenacc`.
- Reduced reproducer with `!$acc enter data &` followed by
  `!$omp flush &` now compiles cleanly.
- Preserved negative mixed-continuation testcase still diagnoses
  `Wrong OpenACC continuation`.
- Focused DejaGnu check passes:
  `goacc.exp=omp-108382.f90`.
- Existing nearby mixed OpenACC/OpenMP coverage still passes:
  `goacc.exp=omp.f95`.
- Broader `goacc.exp` sweep passes with the rebuilt trunk compiler wrapper:
  `3951` expected passes, `281` expected failures, no unexpected results.
- Full `check-gfortran` rerun on `pr108382-fix` finished clean with `0`
  `FAIL` / `XPASS`.
