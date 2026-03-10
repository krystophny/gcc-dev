# Bug 120723: OpenACC scalar `attach`/`detach` ICE

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120723
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/96
- **Branch:** `pr120723-fix`
- **Status:** PATCH READY (signed patch on fork)

## Summary

Standalone OpenACC `attach` and `detach` clauses already have dedicated
lowering for pointer components and descriptor-based arrays, but plain scalar
pointer-like variables still fell through the generic scalar pointer mapping
path.  That path generated a standalone pointer-mapping node, and gimplify
then ICEd with `unexpected pointer mapping node`.

## Reproducer

`reproducer.f90`

Compile:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc \
  -I gcc-build/x86_64-pc-linux-gnu/libgomp \
  -fopenacc -c pr/120723/reproducer.f90
```

Expected result after the fix:

- successful compile
- no internal compiler error

## Local Fix

- In the generic scalar pointer/allocatable path in `trans-openmp.cc`, detect
  bare OpenACC `attach`/`detach` clauses for non-descriptor scalar
  pointer-like variables.
- Lower those clauses as a single attach/detach operation on the pointer
  itself instead of emitting a standalone pointer-mapping node.
- Add `gfortran.dg/goacc/pr120723.f90`, which checks the scalar pointer and
  scalar allocatable forms via the `original` dump.

## Validation

- Direct compile of `reproducer.f90`: PASS
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="goacc.exp=pr120723.f90"`:
  PASS
- Existing descriptor attach test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="goacc.exp=attach-descriptor.f90"`:
  PASS
- Existing invalid-argument diagnostic:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="goacc.exp=pr109622-6.f90"`:
  PASS
- Full `check-gfortran`: PASS (`0` `FAIL`/`XPASS`)

## Review Notes

- The fix is intentionally scoped to the plain scalar path.  Descriptor arrays
  and component attaches already have dedicated bare-attach lowering and were
  left unchanged.
- The new test needed one correction during review: the first draft was
  truncated and then overfit a manual compile dump instead of the testsuite
  `-S` lowering.  The final version matches the actual `goacc.exp` output.
- The new test checks the emitted OpenACC clauses for scalar pointer and
  scalar allocatable items, so it guards against both regressions and future
  refactorings that would reintroduce a standalone pointer-mapping node.

## Patch Artifacts

- GCC commit: `5fae5d7c4e9c25d18c52a14d5ff8779030908ff5`
- Exported patch:
  `pr/120723/0001-fortran-Fix-scalar-OpenACC-attach-detach-lowering-PR.patch`
- Branch: `origin/pr120723-fix`
