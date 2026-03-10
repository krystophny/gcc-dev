# Bug 122491: [16 Regression] ASAN UAF in missing END BLOCK recovery

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122491
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/50
- **Status:** MERGED upstream (`r16-7577-gff2f6c5153ecc1`, commit `ff2f6c5153e`)

## Summary

On invalid source with missing `END BLOCK` (`gfortran.dg/pr103508.f90`),
error recovery in `gfc_match_end` freed a BLOCK namespace too early. That
namespace can still be referenced by parser state/code nodes, causing
heap-use-after-free under sanitizer-instrumented builds.

## Fix

File changed:

- `gcc/fortran/decl.cc`

Change:

- In `gfc_match_end` cleanup for malformed `END` inside `COMP_BLOCK`, do not
  free `gfc_current_ns` immediately.
- Keep existing unlink + unwind to parent state behavior.
- Let normal block unwinding/cleanup own namespace lifetime.

## Attribution

- Reported by Filip Kastl `<fkastl@suse.cz>`
- Suggested by Jakub Jelinek `<jakub@redhat.com>`

## Reproducer

- `pr/122491/reproducer.f90`

Compile command:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only pr/122491/reproducer.f90
```

Expected diagnostics:

- `END BLOCK statement expected` on two lines
- `Unexpected end of file`

## Validation (2026-02-18)

- Rebuilt front end in `gcc-build/gcc`.
- Targeted test: `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=pr103508.f90"` passed.
- Full suite: `make -C gcc-build/gcc -j32 -k check-gfortran` passed with no
  `FAIL`/`XPASS` lines in `gcc-build/gcc/testsuite/gfortran/gfortran.sum`.

## Patch Artifact

- `pr/122491/0001-fortran-Avoid-UAF-on-missing-END-BLOCK-cleanup-PR122.patch`
