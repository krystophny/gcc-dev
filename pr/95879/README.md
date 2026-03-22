# Bug 95879: Use-after-free in gfc_resolve_formal_arglist

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95879
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/69
- **Status:** ON BUGZILLA (patch attached; full validation complete)

## Summary

ICE (or silent use-after-free) when a contained subroutine has a statement
function whose dummy argument name matches a symbol replaced by
`gfc_fixup_sibling_symbols`.

## Root Cause

`gfc_fixup_sibling_symbols` replaces symbols in contained namespaces with
their parent-namespace counterparts and frees the old symbol via
`gfc_release_symbol`.  If the old symbol is also referenced as a dummy
argument of a statement function in the same namespace, the formal argument
list retains a dangling pointer to the freed symbol.

Whether this manifests as a visible crash depends on whether the freed
memory has been reused, making it appear intermittently fixed without an
actual code change.  Confirmed as heap-use-after-free with AddressSanitizer
on all branches including current trunk.

## Fix

Add `fixup_st_func_formals` in `parse.cc` which walks the namespace's
symtree before the old symbol is released and updates any statement function
formal argument references from `old_sym` to the replacement symbol.  Formal
argument lists are non-owning pointers so no reference count adjustment is
needed.

## Patch

- Branch: `pr95879-fix`
- Commit: `e2bb459d5d99d52b2b58656665fe0b9611b601be`
- Patch: `0001-fortran-Fix-use-after-free-in-gfc_fixup_sibling_symb.patch`

## Test Results

- Original reproducer is fixed on the current patch branch.
- Fresh full `check-gfortran` rerun on `pr95879-fix` finished clean with `0`
  `FAIL` / `XPASS`.
