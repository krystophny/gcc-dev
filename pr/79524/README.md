# Bug 79524: stale charlen after rejected parameter array declaration

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=79524
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/55

## Summary

`character(*), parameter :: z(2) = [character(n) :: 'x', 'y']` rejects the
declaration, but the rejection can leave declaration-local `gfc_charlen` nodes
on the namespace `cl_list`.  Later resolution revisits the stale
`character(n)` length expression and, before this fix, could walk freed symbol
state in `resolve_charlen`.

The old local patch tried to make `resolve_charlen` detect dangling symtrees.
Review on Bugzilla pushed back on that approach because it added a namespace
tree walk to resolution and kept the real problem alive longer than necessary.
The fix now cleans up the declaration-local charlens at the rejection point in
`decl.cc`, after clearing the surviving owners in that path.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only pr/79524/reproducer.f90
```

Expected result after the fix:

- user-facing diagnostic only
- no later `Scalar INTEGER expression expected` from the rejected declaration
- no Valgrind invalid read
