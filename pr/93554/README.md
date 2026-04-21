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

Five execution tests under `pr/93554/tests/` cover the three reported
shapes plus two targeted stress scenarios:

| scenario | meta-repo file                                       | upstream name         | compile-baseline | compile-trunk | host-fallback (6 opt lvl) | nvptx-device | runtime free edge |
|----------|------------------------------------------------------|-----------------------|------------------|---------------|---------------------------|--------------|-------------------|
| S1       | `pr93554-private-derived-alloc-component.f90`        | `pr93554-1.f90`       | ICE              | clean         | PASS 6/6                  | PASS         | gated (PTX only)  |
| S2       | `pr107227-private-whole-allocatable.f90`             | `pr107227-1.f90`      | ICE              | clean         | PASS 6/6                  | PASS         | gated (PTX only)  |
| S3       | `pr95550-parallel-create-private.f90`                | `pr95550-1.f90`       | ICE              | clean         | PASS 6/6                  | PASS         | gated (PTX only)  |
| S4 NEW   | `pr93554-alloc-in-body.f90`                          | `pr93554-2.f90`       | ICE              | clean         | PASS 6/6                  | PASS         | reachable at runtime |
| S5 NEW   | `pr93554-private-independence.f90`                   | `pr93554-3.f90`       | ICE              | clean         | PASS 6/6                  | PASS         | reachable at runtime |

S1--S3 exercise `!$acc parallel loop` with explicit `gang`, `worker`,
`vector`, `seq` and `!$acc kernels` variants.  S4 allocates the
private's allocatable component inside the loop body, forcing the
per-thread finaliser `__nvptx_free` to run.  S5 carries a whole
allocatable `buf` through `num_gangs(4)` gang partitioning -- the
OpenACC runtime materialises the per-gang copy on entry, which must
be freed on exit.

Artifacts:

- `verification/env.txt` -- compilers, commit hashes, CUDA/driver.
- `verification/cfg.md` -- CFG analysis (OpenMP control case plus a
  per-test coverage table in the "Coverage" section).
- `verification/matrix.md` -- full matrix, targets, and caveats.
- `verification/host-run.log`, `.log.filtered` -- direct-compile host
  matrix (30 PASS, 0 FAIL).
- `verification/nvptx-run.log` -- offload compile + run (5 PASS, 0 FAIL).
- `verification/nvptx/gomp-debug-pr93554-1.log` -- S1 `GOMP_DEBUG=1`
  trace (5 offload entry points, `__nvptx_free` gated).
- `verification/nvptx/gomp-debug-pr107227-1.log`,
  `verification/nvptx/gomp-debug-pr95550-1.log` -- S2 and S3 traces
  (same gated pattern as S1).
- `verification/nvptx/gomp-debug-pr93554-2.log` -- S4 trace
  (malloc=2, free=1 per offload entry body; free reachable at
  runtime because the component is allocated inside the body).
- `verification/nvptx/gomp-debug-pr93554-3.log` -- S5 trace
  (malloc=1, free=1 per offload entry body; free reachable per gang).
- `verification/nvptx/ptx-malloc-free-summary.txt` -- per-scenario
  call-site scan.
- `verification/provenance-tests.md` -- per-test lineage audit.
- `0002-libgomp-testsuite-OpenACC-Fortran-private-allocatabl.patch` --
  upstream test patch (not yet submitted).
- `dumps/*.018t.ompexp` -- `ompexp` pass dumps for each reproducer.
- `dumps/baseline-ice.log` -- pre-fix ICE backtrace.

## Bounds

- AMD GCN offload is not tested (NVPTX-only local hardware).
- NVPTX runs target `sm_89` PTX JIT-compiled by the driver on a
  Blackwell GPU; no multi-sm_XX matrix -- the fix is architecturally
  neutral at the GCC level.
- `CHUNKS > 1` placement of the finaliser is a pre-existing code
  generation question unaffected by r16-8571.  S4 reaches the free
  edge for every chunk boundary the runtime picks but does not
  assert a specific chunk count.
- Fully-partitioned `gang worker vector` private for whole
  allocatables on NVPTX surfaces a separate issue (writes across
  vector lanes alias through a per-worker private); S5 therefore
  pins to gang-only partitioning to keep the focus on r16-8571.

## Review thread

Thomas Schwinge raised three points on gcc-patches on 2026-04-13:

1. Verify PR95550 and PR107227 are actually resolved -- done, see above.
2. Add execution test cases -- five drafted under `pr/93554/tests/`,
   staged upstream at `libgomp/testsuite/libgomp.oacc-fortran/` on
   branch `pr93554-tests` and exported as
   `0002-libgomp-testsuite-OpenACC-Fortran-private-allocatabl.patch`;
   not yet submitted to gcc-patches.
3. Confirm later passes handle the looser CFG on the device -- the
   new S4 / S5 tests allocate a private inside the body and carry a
   whole-allocatable private through multiple gangs respectively, so
   `__nvptx_free` is reachable at runtime in both offload entry
   bodies; correctness holds at every optimisation level (host
   fallback, NVPTX sm_89).  See `verification/cfg.md` Coverage
   section and `verification/nvptx/ptx-malloc-free-summary.txt`.

GitHub issue #62 carries the running summary.  Nothing has been posted
to Bugzilla or gcc-patches by this round of work.
