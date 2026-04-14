# PR 107721 - Array Constructor Type-Spec Folding

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107721
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/6

**Author:** Christopher Albert
**Co-Author:** Harald Anlauf
**Patch:** `0001-fortran-Honor-array-constructor-type-spec-during-fol.patch`

## Issue Summary

When an array constructor has an explicit type-spec (e.g., `[character(16) :: ...]`), GCC was failing to correctly handle:
1.  Parenthesized elements: `[integer :: ([1.0])]`
2.  Nested constructors: `[[integer :: [1.0]]]`
3.  Concatenation with type-spec: `[character(16) :: 'a', 'b'] // '|'`
4.  **Nested type-specs with different lengths:** `[character(16) :: [character(2) :: 'abcd']]`

## Fix Strategy: "Resolve-Propagate-Resolve"

The core fix is in `gfc_resolve_character_array_constructor`. When a nested array constructor is encountered:
1.  Check if it has its own explicit type-spec.
2.  **First Pass:** If yes, resolve it recursively *using its own type-spec*. This enforces inner truncation/padding (e.g., truncating 'abcd' to 'ab').
3.  **Propagation:** Propagate the outer constructor's type-spec to the inner one.
4.  **Second Pass:** Resolve it recursively *again*. This enforces outer truncation/padding (e.g., padding 'ab' to 'ab              ').
