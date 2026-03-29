# Bug 93715: ICE in gfc_trans_auto_array_allocation with scalar coarray

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93715
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/63
- **Status:** ON BUGZILLA

## Description

A scalar coarray variable used in asynchronous I/O causes an ICE:

```
internal compiler error: in gfc_trans_auto_array_allocation, at fortran/trans-array.cc
```

Reproducer:
```fortran
program p
   integer :: a, b[*]
   read (1, *, asynchronous='yes') a, b
end
```

Compile with: `gfortran -fcoarray=single` or `gfortran -fcoarray=lib`

## Root Cause

In `gfc_trans_deferred_vars`, scalar coarray variables (codimension but no
dimension) enter the `AS_EXPLICIT` switch case because `sym->attr.codimension`
is true and the coarray spec type is `AS_EXPLICIT`.  The existing static
coarray guard (`sym->attr.codimension && TREE_STATIC(...)`) does not catch
non-static scalar coarrays, so they fall through to
`gfc_trans_auto_array_allocation` which asserts `GFC_ARRAY_TYPE_P` -- a
condition that fails for scalar types.

## Fix

Add an explicit check for scalar coarrays (`sym->attr.codimension &&
!sym->attr.dimension`) in `gfc_trans_deferred_vars` to skip array allocation
for variables that have coarray rank but zero array rank.

Regression since GCC 10 (works in GCC 9).

## Verification

### Test fails on trunk
```
$ gfortran -fcoarray=single -c reproducer.f90
reproducer.f90:2:18:

    2 |    integer :: a, b[*]
      |                  1~~~
internal compiler error: in gfc_trans_auto_array_allocation, at fortran/trans-array.cc:7379
```

### Test passes after fix
```
$ gcc-build/gcc/gfortran -B gcc-build/gcc -fcoarray=single -c reproducer.f90
(clean, no output)
```

- `make check-gfortran RUNTESTFLAGS="dg.exp=pr93715.f90"`: PASS
- Full `check-gfortran`: 0 FAIL / XPASS
