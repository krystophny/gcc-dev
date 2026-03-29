# Bug 102333: invalid `PROCEDURE` statement accepted

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/78
- **Status:** upstream `REOPENED`; attachment `64064` is too broad and should be obsoleted; no replacement patch posted

## Summary

The original report was an ICE in `gfc_generate_function_code` for a
contained function declaring `procedure(f)` where the host function `f`
returns an unlimited polymorphic pointer or allocatable result.

That crash no longer reproduces on current trunk or on `gcc-15`. A non-ICE
testcase was committed on 2026-03-12 as `r16-8026-g8a0a1a0c7b1`, but only on
trunk.

Bugzilla was reopened on 2026-03-28 because comment 1 notes that
`procedure(f), allocatable :: z` is invalid and should be rejected.
Re-checking on a clean `upstream/master` build shows that current trunk
already rejects that form. The pointer forms from comments 0 and 2 are still
accepted, but they are ordinary `PROCEDURE(interface), POINTER` declarations,
and Paul Thomas's suggested parser-side `gfc_check_conflict` call does not
change their behavior.

Jerry DeLisle's comment 14, `Fixed on 13, 14, 15, and 16.`, does not match the
current upstream branch heads as of 2026-03-29. Direct reruns show that the old
ICE is still present on `gcc-13` and `gcc-14`.

## Remaining Work

The remaining upstream work is clarification, not code. The posted patch on
`origin/pr102333-fix` rejects valid pointer cases, so it should be obsoleted.
Current evidence says:

- comment 1 is already diagnosed on trunk and `gcc-14`/`gcc-15`
- the old ICE is still present on `gcc-13` and `gcc-14`
- the simpler `decl.cc` suggestion is a no-op for this PR
- there is no standards-based replacement patch to post yet

## Branch Evidence

Upstream branch heads used for the rerun on 2026-03-29:

- `upstream/master`: `a3b49ec48b7749250fe5acf3918bad4c6c4f7a62`
- `upstream/releases/gcc-15`: `9cefb203c4010b139a69f1575fcdec14075d2731`
- `upstream/releases/gcc-14`: `f8cc39faaa3cfa44efb484a60d2eb7684572b85c`
- `upstream/releases/gcc-13`: `e8896d8d6c4275bbd00ae6fba4b3f609e6affaba`

Test sources rerun exactly from Bugzilla:

- comment 0: `/tmp/pr102333-c0.f90`
- comment 1: `/tmp/pr102333-c1.f90`
- comment 2 pointer variant: `/tmp/pr102333-c2a.f90`
- comment 2 allocatable-result host variant: `/tmp/pr102333-c2b.f90`

Observed matrix:

| Branch | c0 | c1 | c2a | c2b |
|---|---|---|---|---|
| `master` | accepted | rejected | accepted | accepted |
| `gcc-15` | accepted | rejected | accepted | accepted |
| `gcc-14` | ICE | rejected | ICE | ICE |
| `gcc-13` | ICE | accepted | ICE | ICE |

This means:

- the original ICE disappeared between `gcc-14` and `gcc-15`
- comment 1 was fixed between `gcc-13` and `gcc-14`
- only trunk has the PR102333 testcase commit

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

Additional branch checks used dedicated worktrees and build directories:

```bash
/home/ert/code/gcc-dev/gcc-build-pr102333-gcc15/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build-pr102333-gcc15/gcc -c /tmp/pr102333-c0.f90
/home/ert/code/gcc-dev/gcc-build-pr102333-gcc14/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build-pr102333-gcc14/gcc -c /tmp/pr102333-c0.f90
/home/ert/code/gcc-dev/gcc-build-pr102333-gcc13/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build-pr102333-gcc13/gcc -c /tmp/pr102333-c0.f90
```

Structural checks:

- `gcc/testsuite/gfortran.dg/pr102333.f90` exists only on `upstream/master`
- `gfc_check_conflict (&current_attr, NULL, &gfc_current_locus);` is absent
  from `decl.cc` on `master`, `gcc-15`, `gcc-14`, and `gcc-13`
