# Bug 106946: ICE on invalid CLASS component in derived type

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=106946
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/88
- **Branch:** `pr106946-fix`
- **Status:** PENDING (patch on fork branch `origin/pr106946-fix`, commit `d02ccf8946c3f4b28a1fa85dba2593eb2a8d0f21`)

## Summary

An invalid CLASS component declaration inside a derived type can leave behind
an orphaned CLASS container symbol during parser error recovery.  The
referenced type gets freed, but the generated CLASS container survives with
dangling pointers and later causes an ICE in resolution.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only pr/106946/reproducer.f90
```

Expected result:

- Diagnostic: `Syntax error in data declaration`
- No internal compiler error

## Fix

Files changed:

- `gcc/fortran/decl.cc`
- `gcc/fortran/symbol.cc`
- `gcc/fortran/gfortran.h`
- `gcc/testsuite/gfortran.dg/pr106946.f90`

Change:

- Record the existing tail of the current derived type component list before
  parsing a data declaration.
- On `MATCH_ERROR` inside a derived type definition, remove any newly-added
  CLASS components created during the failed statement.
- Delete the generated CLASS container symbol from the namespace symtree when
  it is still present, release the symbol, and free the component node.
- Expose `gfc_free_component` and `gfc_delete_symtree` for that rollback path.
- Expand the regression coverage to include allocatable and pointer CLASS
  declarations, plus a valid component followed by a bad one.

## Validation

- Direct compile of the new testcase with `gcc-build/gcc/gfortran -B gcc-build/gcc`:
  PASS (diagnostic only, no ICE).
- Targeted DejaGnu test:
  `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr106946.f90"`:
  PASS.
- Full `check-gfortran`:
  PASS (`0` `FAIL`/`XPASS` lines in `gcc-build/gcc/testsuite/gfortran/gfortran.sum`).

## Patch Artifact

- `pr/106946/0001-fortran-Fix-ICE-on-invalid-CLASS-component-in-derive.patch`
