# GCC PR102430 – OpenMP linear(array) ICE / missing support

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102430
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/9
- **Status:** PENDING (patch on fork, awaiting upstream submission)

**Title:** OpenMP linear clause accepts arrays on worksharing loops

## Summary

Bug 102430 reports an ICE in GCC 13+ when compiling a Fortran OpenMP loop with
`linear(a)` where `a` is an array, e.g. `!$omp parallel do linear(a)`.

Jakub Jelinek’s analysis in the Bugzilla thread indicates that GCC’s
`OMP_CLAUSE_LINEAR_ARRAY` support is only implemented for SIMD constructs, and
that worksharing-loop lowering (`omp-expand.c`) does not handle array linear.

## Key points

- `linear` is not synchronization; it is a privatization rule with a per-iteration
  progression. A list item in `linear` is subject to `private` semantics, and the
  value for each logical iteration is derived from the original value plus the
  iteration number times the linear-step.
- The immediate compiler issue is that the Fortran front end accepts `linear(a)`
  on an array for `parallel do`, but the middle-end OpenMP expansion does not
  implement that case (historically resulting in an ICE).

## Reproducer

`reproducer.f90` is the Bugzilla minimal test case.

Compile with OpenMP enabled:

```bash
./gcc-build/gcc/gfortran -B ./gcc-build/gcc -fopenmp -c pr/102430/reproducer.f90
```

## Patch

- GCC branch: `pr102430-linear-sorry`
- Exported patch: `0001-fortran-Reject-array-allocatable-LINEAR-on-DO-PR1024.patch`

## Status (2026-01-13)

- **Priority:** P2 regression (GCC 13/14/15/16)
- **Patch attached to Bugzilla:** 2025-12-21
- **Rebased on upstream/master:** 2026-01-13
- **Mailing list submission:** Not yet submitted to gcc-patches
- **Stage 4 candidate:** Yes - regression fix with minimal scope

## Fix approach

Rejects array/allocatable items in `linear(...)` on worksharing loops in the
Fortran front end with a "Sorry, not yet supported" error. This prevents the
ICE during OpenMP expansion while leaving the door open for future implementation.
