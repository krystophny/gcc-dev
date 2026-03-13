# Bug 95338: ICE on mixed ENTRY result types with `-ff2c`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95338
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/68
- **Branch:** `pr95338-fix`
- **Status:** MERGED (r16-8014-g490c7ba8d880f)

## Summary

For mixed `ENTRY` functions, the frontend builds a master union result that
stores one field per entry result.  Under `-ff2c`, default `REAL` entries use
the C `double` ABI return type even though their Fortran result symbol remains
default `REAL`.  The union builder currently uses the Fortran symbol type
directly, so the master union stores a `real(kind=4)` field while the entry
wrapper returns `real(kind=8)`.  That leaves a non-trivial conversion inside a
`COMPONENT_REF`, and the GIMPLE verifier rejects the lowered code.

## Reproducer

`reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -O1 -ff2c -c pr/95338/reproducer.f90
```

Expected result after the fix:

- successful compile
- no internal compiler error

## Local Fix

- Add a helper in `trans-types.cc` that computes the ABI result type for an
  entry result field.
- Use that helper when building the mixed-entry master union, so default
  `REAL` entries under `-ff2c` contribute a `real(kind=8)` union member.
- Add `gfortran.dg/pr95338.f90` as a regression test for the original mixed
  `INTEGER`/`REAL` `ENTRY` reproducer under `-O1 -ff2c`.

## Validation

- Direct compile of `reproducer.f90`: PASS
- Direct `-fdump-tree-original` check: PASS (`master.0.f` now uses
  `real(kind=8)` for entry `g`)
- Targeted DejaGnu tests:
  - `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr95338.f90"`: PASS
  - `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=entry_26.f90"`: PASS
  - `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=entry_27.f90"`: PASS
  - `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr104313.f"`: PASS
- Full `check-gfortran`: PASS (`0` `FAIL`/`XPASS` lines in
  `gcc-build/gcc/testsuite/gfortran/gfortran.sum`)

## Review Notes

- The change is intentionally ABI-focused: the entry wrapper signatures were
  already correct, and only the shared master union fields were wrong.
- The helper comment now makes the `-ff2c` ABI rule explicit at the union
  construction site, which is where the subtle mismatch originated.

## Patch Artifact

- `pr/95338/0001-fortran-Fix-mixed-ENTRY-union-ABI-under-ff2c-PR95338.patch`
