# PR123255 - OpenACC: copyin allocatable component ordering regression

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123255

## Summary

On upstream `master` at `769041822723208bf85a91ac409b9b0bdae3fff0`, the
reproducer in `reproducer.f90` runs successfully with OpenACC NVPTX offload.
The `libgomp: invalid size` failure reproduces only with the initial local
gimplify change for PR123252 (commit `42475cae6d7cce30aabfac660a55c2d9e5b38e68`)
that inserted scalar field mappings into the `GOMP_MAP_STRUCT` chain without
preserving struct-member ordering for Fortran descriptors.
The corrected PR123252 patch (commit `853cd89ae61b42fe1bd4e872c46e1e4911f4d399`)
fixes both PR123252 and this regression by inserting added scalar member
mappings into the struct member list in field order (so `c%n` precedes
`c%data`), without splitting descriptor-related nodes.
