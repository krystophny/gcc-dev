# Bug 93554: ICE in expand_oacc_for with private derived type

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93554
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/62
- **Trunk commit:** `r16-8571-g010618b8dcb73220790f8f82cf76e8a2aacc2122`
- **Upstream status:** merged 2026-04-11 (pushed by Jerry DeLisle).

## Root cause

When the `private` clause on an OpenACC loop names a derived type with an
allocatable component (or, per PR95550 / PR107227, a whole allocatable
array), the Fortran front end emits finalisation code inside the
offloaded region.  Those extra basic blocks sit between `cont_bb` and
`exit_bb`, which breaks three CFG assertions in `expand_oacc_for`:

- `BRANCH_EDGE(entry_bb)->dest == exit_bb`
- `FALLTHRU_EDGE(cont_bb)->dest == exit_bb`
- `EDGE_COUNT(exit_bb->preds) == 1 + (cont_bb != NULL)`

## Fix

`gcc/omp-expand.cc` — `expand_oacc_for`: replace the structural
equalities with edge-count invariants and drop the predecessor-count
check on `exit_bb`.  The one remaining structural invariant (`bed ==
body_bb || single_succ_edge(bed)->dest == body_bb`) still holds because
the finalisation chain is inserted off `entry_bb`'s branch edge, not
`cont_bb`'s branch edge.

The change is Burnus's 2020 draft (PR93554 comment #3) plus removal of
the exit-bb predecessor assertion.  Installed regression test:
`gcc/testsuite/gfortran.dg/goacc/pr93554.f90` (compile-only).

## Related PRs resolved by the same fix

- **PR95550** (middle-end): `!$acc parallel create(A) + !$acc loop private(A)`
  on a whole allocatable array.  Also Gribov's simpler
  `!$acc parallel loop private(GWORK)` on a complex allocatable.  Both
  ICE at `omp-expand.cc:7722` on the pre-fix baseline; both compile
  clean on trunk.  See `pr/95550/`.
- **PR107227** (libgomp): `!$acc parallel loop private(arr)` on a whole
  allocatable real array.  Same ICE site; same fix.  See `pr/107227/`.

Both should be closed as DUPLICATE of 93554 once the reviewer has
confirmed the findings.

## Verification

Full evidence is under `pr/93554/verification/`.

**Scope of testing**

| scenario | repro                                                | compile-baseline | compile-trunk | host-fallback              | nvptx-device |
|----------|------------------------------------------------------|------------------|---------------|----------------------------|--------------|
| PR93554  | `pr/93554/repro/derived-alloc-component.f90`         | ICE              | clean         | PASS (-O0..-O3, -Os)       | PASS         |
| PR95550  | `pr/95550/repro/parallel-create-private.f90` and     | ICE              | clean         | PASS (-O0..-O3, -Os)       | PASS         |
|          | `pr/95550/repro/parallel-loop-private.f90`           | ICE              | clean         | n/a (subroutine-only repro)| n/a          |
| PR107227 | `pr/107227/repro/parallel-loop-private.f90`          | ICE              | clean         | PASS (-O0..-O3, -Os)       | PASS         |

Execution coverage comes from three new tests under `pr/93554/tests/`:

- `pr93554-private-derived-alloc-component.f90`
- `pr107227-private-whole-allocatable.f90`
- `pr95550-parallel-create-private.f90`

Each exercises `!$acc parallel loop` with explicit `gang`, `worker`,
`vector`, `seq` and an additional `!$acc kernels` variant, and asserts
post-region values with `stop <N>`.  All variants pass on host fallback
across six optimisation levels, and on NVPTX for `-g -O2`.

Artifacts:

- `verification/env.txt` — compilers, commit hashes, CUDA/driver.
- `verification/cfg.md` — CFG analysis including an OpenMP control case
  (`!$omp parallel do private(x)`) that shows why the OpenMP path never
  tripped the assertions.
- `verification/matrix.md` — the full test matrix and caveats.
- `verification/host-run.log` — filtered PASS lines + libgomp summary
  (6374 passes, 0 new FAIL/XPASS).
- `verification/host-run.log.filtered` — matching lines from full libgomp.log (context beyond the filtered PASS list).
- `verification/nvptx-run.log` — offload compile + run output.
- `verification/nvptx/gomp-debug-pr93554.log` — `GOMP_DEBUG=1` trace
  showing the finalisation is emitted as `__nvptx_free` / `__nvptx_malloc`
  calls inside the device kernel.
- `dumps/*.018t.ompexp` — `ompexp` pass dumps for each reproducer
  (trunk and baseline).
- `dumps/baseline-ice.log` — pre-fix ICE backtrace for PR93554.

## Bounds

- Tests do not allocate the allocatable entity inside the loop body, so
  the finalisation free path is a no-op at runtime.  The PTX emits the
  free regardless, which is what we want to demonstrate.  A stricter
  test that *does* allocate inside the body would also stress the
  `CHUNKS > 1` placement of finalisation; that is a pre-existing code
  generation question, unaffected by this commit.
- AMD GCN offload was not tested (NVPTX-only local hardware).

## Review thread

Thomas Schwinge raised three points on gcc-patches on 2026-04-13:

1. Verify PR95550 and PR107227 are actually resolved — done, see above.
2. Add execution test cases — drafted under `pr/93554/tests/`; not yet
   submitted upstream pending reviewer feedback.
3. Confirm later passes handle the looser CFG — host-fallback and NVPTX
   execution both pass; `GOMP_DEBUG` trace shows finalisation lands on
   device.

GitHub issue #62 carries the running summary.  Nothing has been posted
to Bugzilla or gcc-patches by this round of work.
