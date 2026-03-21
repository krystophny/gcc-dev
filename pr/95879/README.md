# Bug 95879: Use-after-free in gfc_resolve_formal_arglist

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95879
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/69
- **Status:** PENDING (patch on fork, attached to Bugzilla)

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

## Test Results

Full `check-gfortran`: 75270 PASS, 0 FAIL, 0 XPASS.
