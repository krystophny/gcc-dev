# PR 107721 - Array Constructor Type-Spec Folding

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107721
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/6
- **Status:** MERGED (gcc commit c50d263beff)

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

## Verification
A comprehensive test suite (`array_constructor_typespec_1.f90`) has been added covering:
-   Basic types (integer, real, complex, logical) with parentheses.
-   Character arrays with concatenation.
-   Nested array constructors.
-   **Harald's Edge Cases:** Triple nesting, mixed scalar/array, scalar concatenation.
-   **Torture Tests:** Empty constructors, zero-length strings, complex nesting depth.

All tests pass on `x86_64-pc-linux-gnu`.

## Development History
-   **Nov 25:** Initial fix for parentheses and simple concatenation.
-   **Nov 29:** Harald Anlauf identified regression with nested type-specs (`[char(16)::[char(2)::...]]`).
-   **Nov 30:** Implemented "Resolve-Propagate-Resolve" strategy. Added torture tests. Validated against ISO standard behavior.
