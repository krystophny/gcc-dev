# Bug 103367: ICE in gfc_conv_array_initializer with invalid index

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103367
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/84
- **Status:** ON BUGZILLA (attachment 64074)

## Summary

An undefined variable used as an array index in a parameter initializer
expression reaches `gfc_conv_array_initializer` after parameter substitution
with an unexpected expression type, hitting `gcc_unreachable()`.

## Fix

Guard against unexpected expression types by returning a zero-filled
constructor, since the frontend has already diagnosed the error.

## Verification

### Test fails on trunk
```
$ gfortran -c reproducer.f90
internal compiler error: in gfc_conv_array_initializer, at fortran/trans-array.cc:7205
```

### Test passes after fix
```
$ gcc-build/gcc/gfortran -B gcc-build/gcc -c reproducer.f90
(warning only, no ICE)
```

- `make check-gfortran RUNTESTFLAGS="dg.exp=pr103367.f90"`: PASS
- Full `check-gfortran`: 0 FAIL / XPASS
