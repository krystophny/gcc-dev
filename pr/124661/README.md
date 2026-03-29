# Bug 124661: SIGSEGV with -fcheck=bounds from type-bound procedure

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124661
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/112
- **Status:** ON BUGZILLA (attachment 64069)

## Summary

A bounds-checked call through a type-bound procedure could lose the original
descriptor while factoring the class reference. The later bounds-check path then
walked the wrong tree and crashed instead of using the saved descriptor. The
same factoring logic also broke the nested component-array variant reported in
Bugzilla comment 4.

## Fix

- Branch: `pr124661-fix6`
- Commit: `2dd03ae06a4c`
- Patch: `0001-fortran-Fix-factored-descriptors-for-bounds-checked-.patch`
- Bugzilla attachment: `64069`

Keep descriptor factoring local to the saved expression so bounds checks do not
rewrite shared trees and use temporaries before they are initialized. This
keeps the original saved-descriptor fix and also covers the nested
component-array case from comment 4.

## Verification

- Reproducer `pr/124661/reproducer.f90` now runs clean with `-fcheck=bounds`.
- Bugzilla comment-4 variant now runs clean with `-fcheck=bounds`.
- `make check-gfortran RUNTESTFLAGS='dg.exp=pr124661.f90'`
- `make check-gfortran RUNTESTFLAGS='dg.exp=assign_14.f90'`
- Full `check-gfortran`: `0` `FAIL` / `XPASS`
- `make -j32 check-target-libgomp-fortran`: no `FAIL` / `XPASS`
