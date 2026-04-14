# Sparse-set valgrind false positives on non-annotated GCC builds

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124574
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/107

- **Historical related PR:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=33796

## Summary

Running `valgrind` directly on `f951` from a normal GCC build without
`--enable-valgrind-annotations` reports uninitialized-memory errors from
`sparseset_bit_p`.  Current trunk still carries a suppression file for these
warnings in `gcc/testsuite/sparseset.supp`.

The local fix initializes the sparse index vector once in `sparseset_alloc`.
That makes `sparseset_bit_p` probes well-defined even for elements that have
never been inserted, while keeping the dense vector non-cleared so
`sparseset_clear` remains O(1).

## Notes

- 2008 commit `37b87a3a8a7` fixed historical PR33796 by using clearing
  allocation.
- 2012 commit `a9c283a50666` switched sparse sets back to non-clearing
  allocation and relied on valgrind annotations.
- 2026 commit `ac750f1b7f4` added `gcc/testsuite/sparseset.supp` to suppress
  these warnings in a valgrind-wrapped testsuite case.
