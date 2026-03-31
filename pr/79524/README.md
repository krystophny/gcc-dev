# Bug 79524: Heap-use-after-free in resolve_charlen with implicit typing

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=79524
- **Status:** PENDING (patch on fork, branch `pr79524-fix`)

## Description

Compiling the following invalid code **without** `-fimplicit-none` triggers a
heap-use-after-free segfault in `resolve_charlen` -> `gfc_resolve_expr` ->
`check_host_association`:

```fortran
program p
   character(*), parameter :: z(2) = [character(n) :: 'x', 'y']
end
```

With `-fimplicit-none`, symbol `n` is caught as undeclared before the
problematic path is reached (existing test `fimplicit_none_2.f90`).

## Root Cause

1. Parsing `character(n)` inside the array constructor typespec creates a
   charlen node on the namespace `cl_list`, with its `length` expression
   referencing an implicitly typed symbol `n` via a symtree pointer.

2. The declaration fails ("Cannot initialize parameter array with variable
   length elements"), triggering `reject_statement` -> `gfc_undo_symbols`,
   which frees `n`'s symtree via `gfc_delete_symtree`.

3. The charlen node survives on `cl_list` with a dangling `length->symtree`
   pointer (the old `old_cl_list` cleanup mechanism was removed in r243463
   for PR65173/69064/69859/78350).

4. Later, `resolve_types` iterates `cl_list` and calls `resolve_charlen`,
   which calls `gfc_resolve_expr(cl->length)`, which dereferences the freed
   symtree in `check_host_association`.

## Fix

Add a guard in `resolve_charlen` that detects dangling symtree references
before resolution.  Two new helpers:

- `symtree_in_bbt`: walks the namespace symtree BBT checking if a given
  symtree pointer is still present (pointer comparison, no dereference).
- `charlen_has_dangling_reference`: checks if a charlen's length expression
  references a symtree that is no longer in the namespace.

If a dangling reference is detected, the expression is freed and resolution
fails gracefully.

## Affected Versions

| Branch | Affected | Notes |
|--------|----------|-------|
| trunk  | Yes      | Fixed by this patch |
| gcc-15 | Yes      | Same vulnerable code pattern |
| gcc-14 | Yes      | Same vulnerable code pattern |
| gcc-13 | Yes      | Same vulnerable code pattern |

The bug exists since r243463 (2016-12-08) which removed the `old_cl_list`
cleanup mechanism.
