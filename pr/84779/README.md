# Bug 84779: ICE compiling entry_4.f90 with -O1 and -fdefault-integer-8

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84779
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/103
- **Status:** INVESTIGATING (valgrind errors remain on trunk)

## Summary

ICE when compiling `gfortran.fortran-torture/execute/entry_4.f90` with
`-O1` or `-Os` and `-fdefault-integer-8`. The ICE itself no longer
reproduces on GCC 16 trunk, but Jerry DeLisle (2026-03-18) reports
336 valgrind errors persist, indicating underlying memory issues.

## Reduced reproducer (from anlauf, comment #2)

```fortran
function f1 (n)
  integer, intent(in) :: n
  integer :: f1, e1
  f1 = n
  return
entry e1 (n)
  e1 = n + 1
end function

program test
  integer :: f1, e1
  logical(8) :: r
  r = f1(0) == 0
  if (.not. r) stop 1
  r = e1(0) == 1
  if (.not. r) stop 2
end program
```

Compile with: `gfortran -O1 -fdefault-integer-8 reproducer.f90`

## Key findings

- ICE occurs only at `-O1` (and previously `-Os`).
- Adding `-fno-tree-sra` avoids the ICE.
- The visible ICE was fixed as a side-effect of other work, but valgrind
  shows memory corruption remains.
- The ENTRY thunk mechanism with mixed integer sizes is the likely root cause.

## Valgrind analysis (2026-03-18, GCC 16.0.1 r16-9623-g110a8007906, x86_64)

Jerry DeLisle rejected closure citing 336 valgrind errors. Investigation shows
these are **not specific to this bug** -- they are pre-existing IRA sparseset
false positives that appear on any compilation:

```
$ valgrind --trace-children=yes ... gfortran -O1 -fdefault-integer-8 -c pr84779_c13.f90
ERROR SUMMARY: 138 errors from 29 contexts  (f951 subprocess)

$ valgrind --trace-children=yes ... gfortran -O1 -c hello.f90
ERROR SUMMARY: 148 errors from 36 contexts  (f951 subprocess -- MORE errors!)
```

All errors originate in `sparseset_alloc` (malloc, not calloc) -> `sparseset_bit_p`
reading uninitialized memory. This is by design: sparseset membership test reads
the sparse array slot first, then validates via the dense array. The hello world
control has more errors than the bug reproducer.

**Conclusion:** The ICE is genuinely fixed. Valgrind errors are unrelated IRA noise.
Bug can be closed as FIXED with a testcase.
