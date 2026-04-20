# PR107227: verify duplicate-of-93554 on trunk

**Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107227

## Summary

`!$acc parallel loop private(arr)` on a `real, allocatable :: arr(:)`
(Bryngelson 2022-10-12) ICE'd pre-fix at `omp-expand.cc:7722`,
identical site to PR93554.  Schwinge already flagged it as a probable
duplicate in 2022.

## Status

- Pre-fix (parent of 010618b8dcb): ICE.
- Post-fix (trunk, r16-8571): compiles cleanly; execution tests pass on
  host fallback and on NVPTX.

## Evidence

See `pr/107227/README.md` and `pr/93554/verification/`:

- `pr/107227/repro/parallel-loop-private.f90`.
- `pr/107227/dumps/baseline-ice.log` — pre-fix ICE.
- `pr/107227/dumps/parallel-loop-private.f90.018t.ompexp` — post-fix CFG.
- `pr/93554/tests/pr107227-private-whole-allocatable.f90` — execution
  test (gang / worker / vector / seq / kernels).
- `pr/93554/verification/{host-run.log,nvptx-run.log}` — PASS.

## Proposed action

Close as DUPLICATE of PR93554 once a reviewer confirms.  Not posted to
Bugzilla yet.

Meta-repo parent: #62 (PR93554).
