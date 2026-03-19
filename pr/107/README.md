# Sparse-set valgrind false positives on non-annotated GCC builds

- **Bugzilla:** none yet
- **Historical related PR:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=33796
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/107
- **Status:** PATCH READY (local branch `sparseset-valgrind-fix-v2`)

## Summary

Running `valgrind` directly on `f951` from a normal GCC build without
`--enable-valgrind-annotations` reports uninitialized-memory errors from
`sparseset_bit_p`.  Current trunk still carries a suppression file for these
warnings in `gcc/testsuite/sparseset.supp`.

The local fix initializes the sparse index vector once in `sparseset_alloc`.
That makes `sparseset_bit_p` probes well-defined even for elements that have
never been inserted, while keeping the dense vector non-cleared so
`sparseset_clear` remains O(1).

## Validation

Compiler used for validation:

- source: `upstream/master` at `a0d6c3f23cc`
- build: existing non-annotated `gcc-build/gcc/f951`

Before the patch on the non-annotated build:

- `valgrind f951 /tmp/hello84779.f90`: `161 errors from 28 contexts`
- `valgrind f951 pr/84779/reproducer.f90`: `358 errors from 28 contexts`
- `valgrind f951 gcc/testsuite/gfortran.fortran-torture/execute/entry_4.f90`: `3031 errors from 38 contexts`

After commit `6d3ccffc0e8f216a8c691907717aa4fe5b052d92`:

- `valgrind f951 /tmp/hello84779.f90`: `0 errors from 0 contexts`
- `valgrind f951 pr/84779/reproducer.f90`: `0 errors from 0 contexts`
- `valgrind f951 gcc/testsuite/gfortran.fortran-torture/execute/entry_4.f90`: `0 errors from 0 contexts`

## Patch

- branch: `sparseset-valgrind-fix-v2`
- commit: `6d3ccffc0e8f216a8c691907717aa4fe5b052d92`
- patch: `0001-sparseset-Initialize-sparse-indices-for-valgrind-cle.patch`

## Notes

- 2008 commit `37b87a3a8a7` fixed historical PR33796 by using clearing
  allocation.
- 2012 commit `a9c283a50666` switched sparse sets back to non-clearing
  allocation and relied on valgrind annotations.
- 2026 commit `ac750f1b7f4` added `gcc/testsuite/sparseset.supp` to suppress
  these warnings in a valgrind-wrapped testsuite case.
