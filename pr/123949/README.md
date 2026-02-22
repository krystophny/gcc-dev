# Bug 123949: [16 regression] [PDT] ICE in `gfc_match_decl_type_spec` at `decl.cc:4782`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123949
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/49
- **Status:** MERGED upstream (decl.cc fix as `3a17cc11cb5`), follow-up pending

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

## Follow-up: aarch64 LTO bootstrap regression

After the decl.cc fix was merged upstream (`3a17cc11cb5`), Linaro CI reported
an ICE on aarch64 with LTO bootstrap:

```
FAIL: gfortran.dg/pr123949.f90 -O  (internal compiler error: in gfc_conv_constant, at fortran/trans-const.cc:425)
```

**Root cause:** Pre-existing bug in `trans-array.cc` ALLOCATE_PDT_COMP case.
`gfc_se tse` at line 11137 was used without `gfc_init_se(&tse, NULL)`, leaving
`tse.ss` as uninitialized stack garbage. Adjacent blocks (lines 11118, 11149)
both call `gfc_init_se`. The decl.cc fix exposed this by allowing large-KIND
PDT instances to reach code generation for the first time.

Only manifests with LTO-bootstrapped compiler on aarch64 (stack layout
differences expose the UB). Not reproducible with debug builds.

**Fix:** `0001-fortran-Initialize-gfc_se-in-PDT-component-allocatio.patch`
on fork branch `origin/pr123949-init-se-fix` (commit `05159b27621`).

### aarch64 LTO bootstrap verification (2026-02-23)

Tested on Hetzner Cloud CAX41 (16 ARM cores, 32 GB RAM, aarch64).
GCC source at upstream commit `3a17cc11c` with fix applied to
`trans-array.cc`.

```
$ uname -m
aarch64

$ gcc-build-lto/gcc/gfortran --version | head -1
GNU Fortran (GCC) 16.0.1 20260220 (experimental)

$ make -j16 bootstrap  # --with-build-config=bootstrap-lto
EXIT: 0

$ cd gcc-build-lto/gcc
$ make check-gfortran RUNTESTFLAGS="dg.exp=pr123949.f90"
PASS: gfortran.dg/pr123949.f90   -O  (test for excess errors)

# of expected passes		1
```

Unfixed build (same commit, no `gfc_init_se` patch) pending on second VM.

## Notes

- Bugzilla comment #1 reports an earlier related crash location with snapshot
  `20250901` (`gfc_get_symbol_decl`), suggesting latent corruption preceding
  the current ICE point.
- Bugzilla comment #2 confirms reproduction.
