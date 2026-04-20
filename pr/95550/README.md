# Bug 95550: ICE in expand_oacc_for — parallel create(A) + loop private(A)

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95550
- **Status:** NEW on Bugzilla; resolved on trunk by the PR93554 fix
  (`r16-8571-g010618b8dcb`).  Proposed disposition: DUPLICATE of 93554
  once a reviewer agrees.
- **Meta-repo parent:** `pr/93554/`.

## Summary

Two reporters independently observed the same assertion abort in
`expand_oacc_for` on OpenACC private clauses covering allocatable data:

- Burnus (2020-06-05): `integer, allocatable :: A(:)` used with
  `!$acc parallel create(A)` followed by `!$acc loop private(A)`.
- Gribov (2021-09-28): `COMPLEX(8), ALLOCATABLE :: GWORK(:)` used with
  `!$ACC PARALLEL LOOP PRIVATE(GWORK)`.

Both back-traces terminate at the same
`expand_oacc_for:<BRANCH_EDGE(entry_bb)->dest == exit_bb>` assertion
that PR93554 flagged; the Fortran front end is producing the same
finalisation-block shape for the whole allocatable as it does for a
derived type with an allocatable component.

## Reproducers

- `repro/parallel-create-private.f90` — Burnus's program verbatim.
- `repro/parallel-loop-private.f90` — Gribov's simpler subroutine form.

## Before / after

- Pre-fix baseline (`0ea3035ffbf`, parent of 010618b8dcb): both
  reproducers ICE at `omp-expand.cc:7722`.  See
  `dumps/baseline-create-ice.log` and `dumps/baseline-loop-ice.log`.
- Post-fix trunk (contains r16-8571): both compile cleanly.  See
  `dumps/parallel-create-private.f90.018t.ompexp` and
  `dumps/parallel-loop-private.f90.018t.ompexp`.

## Execution

Covered by `pr/93554/tests/pr95550-parallel-create-private.f90`, which
exercises `gang`, `worker`, `vector`, `seq` and an `acc kernels`
variant over a 32-element allocatable.  Results:

- host-fallback (`-O0 .. -O3, -Os`): PASS.
- NVPTX device: PASS.

See `pr/93554/verification/host-run.log` and
`pr/93554/verification/nvptx-run.log`.
