# Bug 123949: [16 regression] [PDT] ICE in `gfc_match_decl_type_spec` at `decl.cc:4782`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123949
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/49
- **Status:** PENDING (patch on fork branch `origin/pr123949-fix`, commit `2b144e4a498`)

## Summary

A parameterized derived type testcase ICEs in GCC 16 front-end parsing:

- `f951: internal compiler error: in gfc_match_decl_type_spec, at fortran/decl.cc:4782`

Bugzilla marks this as a 16 regression and tags it with
`needs-bisection` and `needs-reduction`.

## Reproducer

The testcase from Bugzilla description is stored in:

- `pr/123949/reproducer.f90`
- `pr/123949/reproducer-fujitsu.f90` (original external MRE snapshot)

Compile command:

```bash
gfortran -c -w pr/123949/reproducer.f90
gfortran -c -w pr/123949/reproducer-fujitsu.f90
```

## Local Results (2026-02-17)

- `gfortran 15.2.1 20260209` (system): compiles
- `gcc-offload-build/install/bin/gfortran 16.0.1 20260205`: ICE at
  `gfc_match_decl_type_spec` (`decl.cc:4782`)
- `gcc-build/gcc/gfortran -B gcc-build/gcc` (`16.0.1 20260217`): fixed
  (no ICE)

## Patch Artifacts

- `pr/123949/0001-fortran-Fix-PDT-ICE-with-large-KIND-values-PR123949.patch`

## Verification

- Before fix (`gcc-offload-build/install/bin/gfortran 16.0.1 20260205`):
  `pr123949.f90`, `pdt_85.f03`, and `reproducer-fujitsu.f90` all ICE.
- After fix (`gcc-build/gcc/gfortran -B gcc-build/gcc 16.0.1 20260217`):
  all three compile successfully.
- Full `check-gfortran` run completed with no `FAIL`/`XPASS` lines in
  `gcc-build/gcc/testsuite/gfortran/gfortran.sum`.

## Notes

- Bugzilla comment #1 reports an earlier related crash location with snapshot
  `20250901` (`gfc_get_symbol_decl`), suggesting latent corruption preceding
  the current ICE point.
- Bugzilla comment #2 confirms reproduction.
