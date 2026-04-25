# Bug 123947: [16 regression] ICE in `gfc_build_addr_expr` at `trans.cc:350`

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123947
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/48

## Summary

GCC 16 trunk ICEs on recursive allocatable deep-copy expansion from the full
Bugzilla testcase (`attachment 63564`).

Bugzilla comment #5 (2026-02-18) reported that the first local fix (comment #4
patch) fixed the original crash but introduced a new ICE (`verify_gimple` /
`location references block not in block tree`) on another testcase.

This update replaces that approach with a wrapper-cache redesign that avoids
reusing context-sensitive wrapper address trees and also breaks wrapper
generation ping-pong in mutually recursive type graphs.

## Reproducers

- Bugzilla full and reduced testcases (attachments 63564, 63567): see
  https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123947 (not redistributed
  here - external content with no license grant; download directly).
- `pr/123947/reproducer.f90` (local reproducer)
- `pr/123947/reproducer-reduced.f90` (local reduced testcase)
- Local verification-only (not added 1:1 to testsuite):
  `/tmp/pr123947_local_0583_variant.f90`

## Root Cause

`structure_alloc_comps` helper selection and wrapper handling had two issues:

1. Helper path selection for recursive allocatable arrays needed to stay on
   direct self-recursion only (not arbitrary "seen" mutual recursion).
2. Wrapper reuse needed to be safe across contexts:
   - Caching an `ADDR_EXPR` tree is unsafe across different function contexts.
   - With only direct generation, mutually recursive wrappers can recursively
     regenerate each other without a stable per-type anchor.

## Fix (v2)

Artifacts:

- GCC commit: `841b68e48c4`
- Exported patch:
  `pr/123947/0001-fortran-Fix-recursive-deep-copy-helper-generation-PR.patch`

Files changed:

- `gcc/fortran/trans-array.cc`
- `gcc/testsuite/gfortran.dg/pr123947.f90` (new)
- `gcc/testsuite/gfortran.dg/pr123947_2.f90` (new)

Behavioral changes:

1. Keep direct self-recursion gating for recursive array helper path.
2. Cache helper wrapper `FUNCTION_DECL` per derived type (not `ADDR_EXPR`).
3. Rebuild fresh `ADDR_EXPR` at each use site from cached `FUNCTION_DECL`.
4. Keep wrapper-generation recursion finite across mutually recursive types via
   the per-type `FUNCTION_DECL` cache.
5. Add second regression test (`pr123947_2.f90`) using a non-1:1 locally
   derived source-allocation pattern.
