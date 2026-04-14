# Bug 124666: [UBSAN] io.cc:290:27 runtime error

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124666
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/113

## Summary

`format_lex` accumulates decimal digits with `value = 10 * value + c - '0'`.
Because `+` and `-` are left-associative, this is parsed as
`(10 * value + c) - '0'` and can trigger signed-overflow UBSAN reports while
lexing large repeat counts.

## Fix

- Branch: `pr124666-fix`
- Commit: `b6951283208`
- Patch: `0001-fortran-Fix-signed-overflow-in-format_lex-digit-pars.patch`

Parenthesize the digit conversion in both affected accumulation sites so the
character is converted to its numeric value before it is added to the running
count.
