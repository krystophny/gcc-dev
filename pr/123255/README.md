# PR123255 - OpenACC: copyin allocatable component ordering regression

**Title:** OpenACC: copyin of allocatable array component computes wrong size

**Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123255

**Status:** RESOLVED FIXED (fixed by PR123252 patch)

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

## How to run

Example:

```bash
gfortran -O2 -fopenacc -foffload=nvptx-none pr/123255/reproducer.f90 -o /tmp/pr123255.x
LD_LIBRARY_PATH=/opt/gcc16/lib64 ACC_DEVICE_TYPE=nvidia /tmp/pr123255.x
```

## Evidence (local)

- Upstream master base passes:
  - `/tmp/pr123255_baseline_gcc_head.log`
  - `/tmp/pr123255_baseline_run_repro.log`
  - `/tmp/pr123255_baseline_run_repro_gomp_debug.log`
- Reproduces with the initial PR123252 gimplify patch (bad ordering):
  - `/tmp/pr123255_with_pr123252_gcc_head.log`
  - `/tmp/pr123255_with_pr123252_run_repro.log`
  - Dump excerpt (shows `c.data` before `c.n`): `/tmp/pr123255_with_pr123252-pr123255_with_pr123252_reproducer.f90.010t.omplower`
- Fixed with the updated PR123252 patch (field order preserved):
  - `/tmp/pr123255_after_fix_run.log`
  - Dump excerpt (shows `c.n` before `c.data`): `/tmp/pr123255_after_fix-reproducer.f90.010t.omplower`
