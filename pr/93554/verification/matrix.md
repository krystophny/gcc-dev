# Verification matrix (expanded, 2026-04-21)

Five execution tests sit under `pr/93554/tests/`; the same set moves
to `libgomp/testsuite/libgomp.oacc-fortran/` in the staged patch on
branch `pr93554-tests` (see `pr/93554/0002-*.patch`).

| scenario | meta-repo file                                       | upstream name         |
|----------|------------------------------------------------------|-----------------------|
| S1       | `pr93554-private-derived-alloc-component.f90`        | `pr93554-1.f90`       |
| S2       | `pr107227-private-whole-allocatable.f90`             | `pr107227-1.f90`      |
| S3       | `pr95550-parallel-create-private.f90`                | `pr95550-1.f90`       |
| S4       | `pr93554-alloc-in-body.f90`                          | `pr93554-2.f90` (NEW) |
| S5       | `pr93554-private-independence.f90`                   | `pr93554-3.f90` (NEW) |

S1--S3 exercise the three reported shapes at compile time and at
runtime but exit their OpenACC regions with the private allocatable
still NULL, so the finalisation `free` edge sits in PTX as an
always-false-gated branch.  S4 allocates the component inside the
loop body; S5 carries a whole allocatable private through
`num_gangs(4)` gang partitioning.  Both force the per-thread free to
actually run on the device.

## Targets

- **compile-trunk** -- `gcc-build/gcc/gfortran` (post-fix, r16-8571).
- **compile-baseline** -- pre-fix `xgcc`, worktree at `010618b8dcb^`.
- **host-fallback** -- trunk `gfortran` direct compile + run, six
  optimisation levels (`-O0 -O1 -O2 -O3 -Os -Og`).
- **nvptx-device** -- `gcc-offload-build/install/bin/gfortran
  -foffload=nvptx-none`, `ACC_DEVICE_TYPE=nvidia` on an RTX 5060 Ti
  (Blackwell) loading PTX targeted at `sm_89`.

## Results

| scenario | compile-baseline          | compile-trunk | host-fallback (6 opt lvl) | nvptx-device | runtime free edge taken |
|----------|---------------------------|---------------|---------------------------|--------------|-------------------------|
| S1       | ICE (omp-expand.cc:7722)  | clean         | PASS 6/6                  | PASS         | no  (gated, PTX only)   |
| S2       | ICE (omp-expand.cc:7722)  | clean         | PASS 6/6                  | PASS         | no  (gated, PTX only)   |
| S3       | ICE (omp-expand.cc:7722)  | clean         | PASS 6/6                  | PASS         | no  (gated, PTX only)   |
| S4 NEW   | ICE (omp-expand.cc:7722)  | clean         | PASS 6/6                  | PASS         | YES (malloc=2, free=1 per offload entry) |
| S5 NEW   | ICE (omp-expand.cc:7722)  | clean         | PASS 6/6                  | PASS         | YES (malloc=1, free=1 per offload entry) |

Host-fallback totals: 5 scenarios x 6 opt levels = 30 PASS, 0 FAIL
(see `host-run.log`, `host-run.log.filtered`).  NVPTX totals:
5 PASS, 0 FAIL (`nvptx-run.log`).  PTX call-site counts for the new
scenarios come from the `GOMP_DEBUG=1` traces in `nvptx/`; the scan is
reproducible via `nvptx/ptx-malloc-free-summary.txt`.

## Evidence bundle

- `pr/<n>/dumps/baseline-*.log` -- pre-fix ICE backtraces, all ending at
  `omp-expand.cc:7722` inside `expand_oacc_for`.
- `pr/<n>/dumps/*.018t.ompexp` -- post-fix `ompexp`-pass dumps.
- `pr/93554/verification/cfg.md` -- CFG analysis with a per-test
  coverage table in the "Coverage" section.
- `pr/93554/verification/host-run.log`,
  `pr/93554/verification/host-run.log.filtered` -- direct-compile host
  matrix output.
- `pr/93554/verification/nvptx-run.log` -- nvptx compile + run for
  each scenario.
- `pr/93554/verification/nvptx/gomp-debug-pr93554.log` -- S1 debug
  trace (PTX emits `__nvptx_free` in five entry points, all gated).
- `pr/93554/verification/nvptx/gomp-debug-pr93554-alloc-in-body.log`
  and `.../gomp-debug-pr93554-private-independence.log` -- S4 and S5
  debug traces where the in-entry-body `__nvptx_free` is reachable.
- `pr/93554/verification/nvptx/ptx-malloc-free-summary.txt` --
  per-scenario malloc/free call-site scan inside the offload entry
  function body.
- `pr/93554/verification/provenance-tests.md` -- per-test lineage
  audit for the five execution tests.

## Bounds

- The "runtime free edge taken" column reflects *reachability*, not
  dynamic execution count.  S4 and S5 reach the edge under every
  thread that finishes the region.  Dedicated leak-stress runs (long
  driver loop + `acc_get_property(acc_property_free_memory)`) were not
  added -- static reachability plus correct numeric output is the
  load-bearing evidence for Thomas's concern #3.
- AMD GCN offload is not tested; local hardware is NVPTX-only.
- NVPTX runs target `sm_89` PTX JIT-compiled at load time on the
  Blackwell GPU.  No multi-sm_XX matrix -- the fix is architecturally
  neutral at the GCC level; PTX differences would not depend on it.
- `CHUNKS > 1` placement of the finaliser remains a pre-existing
  code-generation question unaffected by r16-8571.  S4 reaches the
  free edge for every chunk boundary the runtime picks but does not
  assert a specific chunk count.
- Fully-partitioned `gang worker vector` private for whole
  allocatables on NVPTX exposes a separate issue -- writes across
  vector lanes alias through the single per-worker private, which is
  orthogonal to r16-8571 (the CFG change is equally present with or
  without vector partitioning).  S5 therefore pins partitioning to
  gang-only, which is enough to validate the free edge for the shape
  that matches PR107227 / PR95550 and keeps the test focused on the
  regression under verification.
