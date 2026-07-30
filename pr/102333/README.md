# Bug 102333: invalid `PROCEDURE` statement accepted

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333
- **Attachment:** https://gcc.gnu.org/bugzilla/attachment.cgi?id=65178
- **Submission comment:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333#c26
- **GitHub issue:** https://github.com/lazy-fortran/gcc/issues/7
- **Fork PR:** https://github.com/lazy-fortran/gcc/pull/37
- **Branch commit:** `6aa15e2df832aab8d05b895b9709895cfdb38d78`

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

The current patch addresses the separate misleading diagnostic reported in
comment 22. It checks the `PROCEDURE` and `ALLOCATABLE` conflict before the
function result is redirected to a hidden procedure pointer result. The test
is a local rewrite with different names and an added valid pointer case.
