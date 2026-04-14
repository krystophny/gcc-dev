# Bug 103367: ICE in gfc_conv_array_initializer with invalid index

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103367
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/84

## Summary

An undefined variable used as an array index in a parameter initializer
expression is invalid Fortran, but current trunk accepts it far enough that
it reaches `gfc_conv_array_initializer` with an unsimplified parenthesized
parameter subobject reference and hits `gcc_unreachable()`.

## Fix

The previous patch was a lowering fallback in `gfc_conv_array_initializer`
that returned an empty constructor for unexpected expression kinds.  That
only masked the ICE after invalid code had already escaped semantic checks.

The replacement fix rejects parameter references that survive
initialization-expression simplification in `gfc_check_init_expr`, so the
invalid source is diagnosed before lowering.  The testcase is therefore a
negative `dg-error` test, not a compile-success test.

## Notes

The invalid-code acceptance predates the March 29, 2026 patch.  It is present
in the original 2021 bug report.  Attachment 64166 therefore supersedes the
old lowering workaround in attachment 64074 on the existing Bugzilla thread.
