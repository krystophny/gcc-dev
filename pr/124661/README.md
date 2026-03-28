# Bug 124661: SIGSEGV with -fcheck=bounds from type-bound procedure

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124661
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/112
- **Status:** PENDING (patch on fork; not yet posted to Bugzilla)

## Summary

A bounds-checked call through a type-bound procedure could lose the original
descriptor while factoring the class reference. The later bounds-check path then
walked the wrong tree and crashed instead of using the saved descriptor.

## Fix

- Branch: `pr124661-fix4`
- Commit: `96e43eec01c`
- Patch: `0001-fortran-Fix-descriptor-factoring-for-bounds-checked-.patch`

Keep the saved descriptor when stripping an `INDIRECT_REF` in
`set_factored_descriptor_value`, and use `info->descriptor` for the later
data/offset accesses in `gfc_conv_ss_descriptor`.

## Verification

- Reproducer `/tmp/pr124661.f90` now runs clean with `-fcheck=bounds`.
- `make check-gfortran RUNTESTFLAGS='dg.exp=pr124661.f90'`
- `make check-gfortran RUNTESTFLAGS='dg.exp=assign_14.f90'`
- Full `check-gfortran`: `0` `FAIL` / `XPASS`

