# Bug 108382: mixed OpenACC/OpenMP continuation misparse

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=108382
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/110

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

## Notes

- Current trunk still reproduces the free-form bug with both the original
  `declare` example and a smaller `enter data` / `flush release` reduction.
- The fixed-form variant from the Bugzilla comment does not reproduce in the
  current local build, so the local fix is intentionally limited to the
  free-form scanner path for now.
