# PR95550: verify duplicate-of-93554 on trunk

**Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95550

## Summary

`!$acc parallel create(A) + !$acc loop private(A)` on a whole allocatable
array (Burnus 2020-06-05) and `!$acc parallel loop private(GWORK)` on a
complex allocatable (Gribov 2021-09-28) both ICE pre-fix at
`omp-expand.cc:7722` — identical site to PR93554.

## Status

- Pre-fix (parent of 010618b8dcb): ICE on both reproducers.
- Post-fix (trunk, r16-8571): both compile cleanly; execution tests pass
  on host fallback and on NVPTX.

## Evidence

See `pr/95550/README.md` and `pr/93554/verification/`:

- `pr/95550/repro/parallel-create-private.f90` and
  `pr/95550/repro/parallel-loop-private.f90`.
- `pr/95550/dumps/baseline-{create,loop}-ice.log` — pre-fix ICE.
- `pr/95550/dumps/*.018t.ompexp` — post-fix CFG.
- `pr/93554/tests/pr95550-parallel-create-private.f90` — execution test
  (gang / worker / vector / seq / kernels).
- `pr/93554/verification/{host-run.log,nvptx-run.log}` — PASS.

## Proposed action

Close as DUPLICATE of PR93554 once a reviewer confirms.  Not posted to
Bugzilla yet.

Meta-repo parent: #62 (PR93554).
