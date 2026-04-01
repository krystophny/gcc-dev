# Bug 124751: Wrong-code after packing assumed-rank actuals for contiguous dummies

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124751
- **Status:** ON BUGZILLA (attachment 64117)
- **Origin:** Follow-up to https://gcc.gnu.org/bugzilla/show_bug.cgi?id=100194

## Description

`PR100194` was fixed on April 1, 2026 by
`r16-8375-g89293f0c2c091db384a7519e4ed56e8f37ef403f`, which removed the
original ICE for assumed-rank actual arguments passed to contiguous
assumed-rank dummies.

That change left a wrong-code regression in the new repacking path.
The frontend packs the data with `_gfortran_internal_pack`, but for
assumed-rank descriptors it reused stale stride and offset metadata from
the original noncontiguous actual argument.

The fix builds a descriptor for the packed temporary before the call.

## Affected Versions

| Branch | Reproduces? | Notes |
|--------|-------------|-------|
| trunk (r16-8375) | yes | Wrong-code after the ICE fix from `PR100194` |
| releases/gcc-15 | no | Regression introduced by the trunk-only `r16-8375` change |
| releases/gcc-14 | no | Regression introduced by the trunk-only `r16-8375` change |
| releases/gcc-13 | no | Regression introduced by the trunk-only `r16-8375` change |

## Validation

- `gfortran -fPIE -B gcc-master-build/gcc -c /tmp/pr100194_paul.f90 -o /tmp/pr100194_paul_pie.o && gfortran /tmp/pr100194_paul_pie.o -o /tmp/pr100194_paul_trunk && /tmp/pr100194_paul_trunk`
- `make -C gcc-master-build/gcc check-gfortran RUNTESTFLAGS='dg.exp=pr100194.f90'`
- `make -C gcc-master-build/gcc -j32 -k check-gfortran > /tmp/check-gfortran-pr100194.log 2>&1`
- `make -C gcc-master-build -j32 check-target-libgomp-fortran > /tmp/libgomp-fortran-pr100194.log 2>&1`

Results:

- `check-gfortran`: `0` `FAIL` / `XPASS`
- `check-target-libgomp-fortran`: `0` `FAIL` / `XPASS`
- Both `libgomp.fortran/fortran.exp` and `libgomp.oacc-fortran/fortran.exp` ran
