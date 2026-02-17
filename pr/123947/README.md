# Bug 123947: [16 regression] ICE in `gfc_build_addr_expr` at `trans.cc:350`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123947
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/48
- **Branch:** `pr123947-fix`
- **Status:** FIXED locally (patch on fork), pending upstream

## Summary

GCC 16 trunk crashes with an ICE (`Segmentation fault`) while compiling the
full recursive-type testcase from Bugzilla attachment 63564. The stack trace
points to:

- `contains_struct_check` (`tree.h`)
- `gfc_build_addr_expr` (`gcc/fortran/trans.cc:350`)

Reported behavior in Bugzilla:

- `gfortran 15.2.0`: compiles testcase
- `gfortran trunk (2026-01-02 and 2026-01-31 snapshots)`: ICE

## Reproducers

Saved Bugzilla attachments:

- `pr/123947/attachment-63564-full.f90` (original full testcase)
- `pr/123947/attachment-63567-mre.f90` (reduced testcase)
- `pr/123947/reproducer.f90` (copy of reduced testcase)
- `pr/123947/reproducer-reduced.f90` (new 23-line local MRE that reproduces)

Compile command:

```bash
gfortran -c -w pr/123947/attachment-63564-full.f90
gfortran -c -w pr/123947/attachment-63567-mre.f90
```

Expected crash location when reproducing:
`ALLOCATE(OBJ_BASE%OBJ(2)%NODE6(3))` in the full testcase.

## Local Results (2026-02-17, clean non-offload rebuild)

Compiler under test:

- `gcc-build/gcc/gfortran -B gcc-build/gcc`
- `GNU Fortran (GCC) 16.0.1 20260217 (experimental)`
- Configured with:
  `--enable-languages=fortran --disable-multilib --disable-bootstrap`

Results on unfixed compiler:

- Reduced testcase (`attachment-63567-mre.f90`):
  - single run: PASS
  - stress loop (30 runs): **30 PASS / 0 FAIL**
- Full testcase (`attachment-63564-full.f90`):
  - single run: FAIL (ICE)
  - stress loop (30 runs): **0 PASS / 30 FAIL**
- Baseline system compiler (`GNU Fortran (GCC) 15.2.1 20260209`):
  - reduced testcase: PASS
  - full testcase: PASS

## Notes

- Bugzilla comment #1 references `r16-5067-g9636d90e432600` as a regression
  marker.
- Bugzilla comment #3 notes the ICE was not observed under valgrind (but very
  slow), and recursive/mutual recursion in type declarations may be relevant.
- Backtrace on failing local build includes:
  - `gfc_build_addr_expr` (`gcc/fortran/trans.cc:350`)
  - `structure_alloc_comps` (`gcc/fortran/trans-array.cc:11053`)
  - `gfc_copy_alloc_comp` (`gcc/fortran/trans-array.cc:11535`)

## Fix

- Commit: `da5c252c8252356e4eb32bead1c231e019f5a430`
- Patch: `pr/123947/0001-fortran-Avoid-ICE-in-recursive-allocatable-deep-copy.patch`

Change summary:

- Restrict recursive array helper path in `structure_alloc_comps` to direct
  self-recursion (instead of any seen/mutually-recursive type).
- Cache generated element-copy helper wrappers per derived type in
  non-coarray mode.
- Add regression test `gcc/testsuite/gfortran.dg/pr123947.f90`.

Validation on patched compiler:

- `attachment-63564-full.f90`: PASS (single run), PASS (30/30 loop)
- `reproducer-reduced.f90`: PASS (single run), PASS (30/30 loop)
- testsuite: `gfortran.dg/pr123947.f90` PASS
