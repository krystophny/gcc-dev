# Sparse-set valgrind false positives on non-annotated GCC builds

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124574
- **Historical related PR:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=33796
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/107
- **Status:** LOCAL FOLLOW-UP (no GCC Bugzilla PR; patch exists locally, validation complete)

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

Full local regression comparison:

- patched build dir: `gcc-regtest-build`
- baseline build dir: `gcc-regtest-base-build`
- source baseline: `upstream/master` at `a0d6c3f23cc`
- configure: `--enable-languages=c,c++,fortran,lto --disable-multilib --disable-bootstrap --enable-valgrind-annotations CFLAGS='-Og -g' CXXFLAGS='-Og -g'`
- test command: `make -j32 -k check`

Normalized `FAIL`/`XPASS` outcome comparison of the full logs:

- patched-only outcomes: `0`
- baseline-only outcomes: `1`

The single baseline-only outcome was:

- `gfortran.dg/coarray/send_array.f90 -fcoarray=lib -pthread -O2 -lcaf_shmem -lrt execution test`

That full-run baseline failure was a timeout only.  A direct rerun of
`caf.exp=send_array.f90` immediately afterward passed in both the patched and
baseline builds, so it is treated as flaky/environmental noise rather than a
real delta caused by the sparse-set patch.

## Patch

- branch: `sparseset-valgrind-fix-v2`
- commit: `6d3ccffc0e8f216a8c691907717aa4fe5b052d92`
- patch: `0001-sparseset-Initialize-sparse-indices-for-valgrind-cle.patch`
- Bugzilla attachment: `63971`

## Notes

- 2008 commit `37b87a3a8a7` fixed historical PR33796 by using clearing
  allocation.
- 2012 commit `a9c283a50666` switched sparse sets back to non-clearing
  allocation and relied on valgrind annotations.
- 2026 commit `ac750f1b7f4` added `gcc/testsuite/sparseset.supp` to suppress
  these warnings in a valgrind-wrapped testsuite case.
