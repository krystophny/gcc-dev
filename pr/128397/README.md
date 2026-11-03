# Bug 128397: Uninitialized extent of automatic array sized by SIZE of another

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128397
- **Issue:** https://github.com/lazy-fortran/gcc/issues/48
- **Fix PR:** https://github.com/lazy-fortran/gcc/pull/49
- **PR-link comment:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128397#c1

## Summary

An automatic object whose bounds or length use SIZE, UBOUND or LEN of
another automatic object gets an uninitialized extent when a contained
procedure references it. The contained procedures are translated before
the host's local variables, so that reference creates the dependent
object's decl, and queues its setup, first. `gfc_defer_symbol_init` kept
non-dummy variables in creation order.

The fix keeps automatic objects (explicit shape with non-constant bounds,
or non-constant character length) in reverse declaration order in the
deferred-init chain; their setup code is prepended, so it runs in
declaration order. Other variables keep the old order: reordering all
locals changed the end-of-scope finalization order that
`finalize_17.f90` checks.

`reproducer.f90` is the reduced testcase posted on Bugzilla. The
testsuite case `pr128397.f90` is a separate rewrite that also covers
UBOUND and a character length.

The patch changes 24 lines outside the testsuite, above the 14-line limit
that `gcc-workflow.py ai-eligibility` enforces for LLM-derived code, so
it is fork-only and is not attached on Bugzilla. Dependencies on an
old-style function result (the `fn_result_dep` path from PR59104) still
keep creation order and are not fixed here.
