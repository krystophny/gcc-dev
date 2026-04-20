# Verification matrix

Scenarios (each in `pr/93554/tests/`):

- **S1** — `pr93554-private-derived-alloc-component.f90`: derived type with
  allocatable component, `private` on OpenACC loop.
- **S2** — `pr107227-private-whole-allocatable.f90`: whole allocatable array,
  `private` on OpenACC loop.
- **S3** — `pr95550-parallel-create-private.f90`: `acc parallel create(A)`
  combined with `acc loop private(A)`.

Parallelism levels exercised per scenario: gang / worker / vector / seq on
`!$acc parallel loop`, plus a `!$acc kernels` + `!$acc loop` case.

Targets:

- **compile-trunk** — `gcc-build/gcc/gfortran` (post-fix, r16-8571).
- **compile-baseline** — pre-fix `xgcc`, worktree at `010618b8dcb^`.
- **host-fallback** — `make check-DEJAGNU` with unix target
  (`-foffload=disable`, `-DACC_DEVICE_TYPE_host=1`, `-DACC_MEM_SHARED=1`).
- **nvptx-device** — direct run with
  `-foffload=nvptx-none`, `ACC_DEVICE_TYPE=nvidia` on an sm_89 GPU.

## Results

| scenario | compile-baseline | compile-trunk | host-fallback                 | nvptx-device |
|----------|------------------|---------------|-------------------------------|--------------|
| S1       | ICE (omp-expand.cc:7722) | clean | PASS across -O0..-O3,-Os | PASS |
| S2       | ICE (omp-expand.cc:7722) | clean | PASS across -O0..-O3,-Os | PASS |
| S3       | ICE (omp-expand.cc:7722) | clean | PASS across -O0..-O3,-Os | PASS |

Each host-fallback cell represents 6 optimisation levels × 2 per test (excess
errors check + execution) = 12 PASS records per scenario; see
`host-run.log` for the verbatim PASS lines.

## Supporting evidence

- `pr/<n>/dumps/baseline-*.log` — pre-fix ICE backtraces, all ending at
  `omp-expand.cc:7722` inside `expand_oacc_for`.
- `pr/<n>/dumps/*.018t.ompexp` — post-fix `ompexp`-pass dumps for each
  scenario.
- `pr/93554/verification/cfg.md` — CFG analysis demonstrating where the
  finalisation blocks land and why the pre-fix assertions no longer hold.
- `pr/93554/verification/host-run.log` — filtered PASS lines plus the
  libgomp summary totals (6374 passes, 0 new FAIL/XPASS, 214 existing
  XFAIL, 188 unsupported).
- `pr/93554/verification/host-run.log.full` — full `libgomp.log`.
- `pr/93554/verification/nvptx-run.log` — compile + run output for each
  test on the offload toolchain, host fallback and nvidia device.
- `pr/93554/verification/nvptx/gomp-debug-pr93554.log` — `GOMP_DEBUG=1`
  run on NVPTX for S1.  The PTX preamble shows entry points for all
  five loop variants (gang/worker/vector/seq/kernels) and contains
  explicit `call __nvptx_free` / `call __nvptx_malloc` inside the
  device kernel, confirming that the finalisation path observed in the
  post-fix CFG is actually emitted into the device image rather than
  dropped on the host side.

## Bounds of this verification

- The fix is a structural assertion relaxation in the middle-end OpenACC
  expander.  Host and NVPTX execution both produce correct results for
  all tested variants, which rules out an obvious class of follow-on
  miscompiles (missing frees, scrambled private storage, wrong loop
  trip count).
- The `GOMP_DEBUG` trace confirms finalisation runs on the device.  It
  does **not** prove optimal placement: under `CHUNKS > 1`, the emitted
  free lives inside the chunk loop (see `cfg.md`).  The current tests do
  not stress that — they do not allocate the component or whole array
  inside the loop body, so the free branch is a no-op at runtime.  This
  is a separate, pre-existing code-generation question unaffected by
  this commit; flagging it as a follow-up if someone chooses to explore
  it.
- AMD GCN offload was not tested — the local box is NVPTX-only.
