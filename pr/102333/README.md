# Bug 102333: invalid `PROCEDURE` statement accepted

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/78
- **Status:** upstream `REOPENED`; attachment `64064` is too broad and should be obsoleted; no replacement patch posted

## Summary

The original report was an ICE in `gfc_generate_function_code` for a
contained function declaring `procedure(f)` where the host function `f`
returns an unlimited polymorphic pointer or allocatable result.

That crash no longer reproduces on current trunk. A non-ICE testcase was
committed on 2026-03-12 as `r16-8026-g8a0a1a0c7b1`.

Bugzilla was reopened on 2026-03-28 because comment 1 notes that
`procedure(f), allocatable :: z` is invalid and should be rejected.
Re-checking on a clean `upstream/master` build shows that current trunk
already rejects that form. The pointer forms from comments 0 and 2 are still
accepted, but they are ordinary `PROCEDURE(interface), POINTER` declarations,
and Paul Thomas's suggested parser-side `gfc_check_conflict` call does not
change their behavior.

## Remaining Work

The remaining upstream work is clarification, not code. The posted patch on
`origin/pr102333-fix` rejects valid pointer cases, so it should be obsoleted.
Current evidence says:

- comment 1 is already diagnosed on trunk
- the simpler `decl.cc` suggestion is a no-op for this PR
- there is no standards-based replacement patch to post yet

## Local Validation

On 2026-03-29, with a clean `upstream/master`-derived build in
`gcc-build-pr102333-alt`:

```bash
gcc-build-pr102333-alt/gcc/gfortran -B gcc-build-pr102333-alt/gcc -c /tmp/pr102333-c0.f90
gcc-build-pr102333-alt/gcc/gfortran -B gcc-build-pr102333-alt/gcc -c /tmp/pr102333-c1.f90
gcc-build-pr102333-alt/gcc/gfortran -B gcc-build-pr102333-alt/gcc -c /tmp/pr102333-c2a.f90
gcc-build-pr102333-alt/gcc/gfortran -B gcc-build-pr102333-alt/gcc -c /tmp/pr102333-c2b.f90
```

the outcomes are:

- comment 0 reproducer: accepted
- comment 1 `procedure(f), allocatable :: z`: rejected with `PROCEDURE attribute conflicts with ALLOCATABLE attribute`
- comment 2 pointer form: accepted
- comment 2 allocatable-result host + pointer declaration: accepted

The existing upstream testcase for the invalid allocatable case also still
passes:

```bash
cd gcc-build-pr102333-alt/gcc
make -j32 check-gfortran RUNTESTFLAGS='dg.exp=proc_decl_1.f90'
```

with `PASS: gfortran.dg/proc_decl_1.f90 ... (line 46)`, which is the existing
`PROCEDURE`/`ALLOCATABLE` conflict check.
