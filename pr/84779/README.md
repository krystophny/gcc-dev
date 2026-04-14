# Bug 84779: ICE compiling entry_4.f90 with -O1 and -fdefault-integer-8

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84779
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/103

## Summary

The original ICE is gone on current GCC 16 trunk: both the original
`gfortran.fortran-torture/execute/entry_4.f90` testcase and the mixed-result
reducer from comment #13 compile and run cleanly with `-O1 -fdefault-integer-8`.

The remaining question from the March 2026 Bugzilla discussion is the direct
`f951` valgrind output.  That reproduces locally, but the errors are not
specific to PR84779 itself.  They all come from generic IRA/LRA sparse-set
membership checks reading memory that GCC intentionally leaves uninitialized
unless the compiler is built with valgrind annotations enabled.

## Direct `f951` valgrind results on the non-annotated build

Running valgrind directly on `f951`, matching Jerry's March 19, 2026
clarification, reproduces the memcheck warnings locally:

```text
$ valgrind --tool=memcheck --track-origins=yes --error-limit=no -s \
    gcc-build/gcc/f951 /tmp/pr84779-comment13.f90
ERROR SUMMARY: 358 errors from 28 contexts

$ valgrind --tool=memcheck --track-origins=yes --error-limit=no -s \
    gcc-build/gcc/f951 gcc/gcc/testsuite/gfortran.fortran-torture/execute/entry_4.f90
ERROR SUMMARY: 3031 errors from 38 contexts

$ valgrind --tool=memcheck --track-origins=yes --error-limit=no -s \
    gcc-build/gcc/f951 /tmp/hello84779.f90
ERROR SUMMARY: 161 errors from 28 contexts
```

The PR84779 inputs produce more errors than hello-world because they generate
more functions and more register-allocation work, but the stacks are the same:

- `sparseset_bit_p` in [`gcc/gcc/sparseset.h`](../../gcc/gcc/sparseset.h)
- allocations from `sparseset_alloc` in [`gcc/gcc/sparseset.cc`](../../gcc/gcc/sparseset.cc)
- callers in IRA/LRA (`ira-lives.cc`, `lra-lives.cc`)

No PR84779-specific `ENTRY` stack frames appear in the valgrind contexts.

## Where the valgrind warnings come from

`sparseset_alloc` intentionally uses non-clearing allocation and then marks the
memory as defined for valgrind:

- [`gcc/gcc/sparseset.cc`](../../gcc/gcc/sparseset.cc): lines 35-39
- [`gcc/gcc/sparseset.h`](../../gcc/gcc/sparseset.h): line 146 reads
  `s->sparse[e]` before checking whether the slot is valid

That is expected sparse-set behavior.  It is only valgrind-clean when the
compiler is built with valgrind annotations enabled.  In this local build:

- `gcc-build/gcc/auto-host.h` contains `/* #undef ENABLE_VALGRIND_ANNOTATIONS */`
- therefore `VALGRIND_DISCARD(...)` compiles to a no-op in
  [`gcc/gcc/system.h`](../../gcc/gcc/system.h)

So the warnings are coming from the current build configuration, not from a new
master regression in the Fortran frontend.

## Related history

- Historical related bug: **PR33796** ("valgrind error with -O2 for linux kernel
  code"), fixed in 2008 by switching sparse sets to clearing allocation.
- Later change: commit `a9c283a50666` (2012-08-18) switched sparse sets back to
  non-clearing allocation for performance and added the valgrind annotation path
  in `sparseset_alloc`.

That means the present warnings are an old known class of sparse-set memcheck
noise resurfacing on builds without valgrind annotations.

## Clean trunk bisection

A clean bisection was run on trunk history with a fresh build at every step.
The test harness treated a revision as:

- bad: either reproducer ICEs with `-O1 -fdefault-integer-8`
- good: both reproducers compile cleanly

Confirmed boundary:

- `600cab162c56` (2024-11-19 parent): bad, fresh build still ICEs
- `694613a7f9ad` (2024-11-19): good, fresh build compiles both reproducers

First good commit for PR84779's visible ICE:

- `694613a7f9adfa9c87e733adc63839c8801f2b5c`
  `expand: Fix up ICE on VCE from _Complex types to _BitInt [PR117458]`

That commit changes only `gcc/expr.cc`.  It adds a guard in
`expand_expr_real_1` so `extract_bit_field` is not called directly on a
non-memory complex operand; instead the operand is first forced into memory and
only then extracted.

This matches the old PR84779 crash exactly.  The bad-build stack is:

- `gen_lowpart_general`
- `extract_bit_field`
- `expand_expr_real_1` in `expr.cc:12509`
- `expand_return`

So PR84779 was not fixed by recent Fortran `ENTRY` work such as PR95338.
Instead, the Fortran testcase was one more frontend route into an already-filed
generic middle-end bug in RTL expansion.

## Related bug already filed

Yes.  The underlying generic bug is already filed as:

- **PR117458:** `ICE: in gen_lowpart_general, at rtlhooks.cc:63 when reinterpreting _Complex float as _BitInt(33)`

URL: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=117458

PR84779 is therefore best understood as a Fortran-specific manifestation of the
same middle-end failure class, not as a remaining unfixed trunk bug and not as
a sparse-set valgrind problem.

## Separate follow-up

The sparse-set valgrind problem is now tracked separately in the local meta
repo:

- GitHub issue: https://github.com/krystophny/gcc-dev/issues/107
- local notes: `pr/107/README.md`
