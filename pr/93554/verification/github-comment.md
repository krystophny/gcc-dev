## Verification follow-up for r16-8571 (PR93554 / PR95550 / PR107227)

Thomas Schwinge raised three concerns on gcc-patches (2026-04-13):

1. confirm PR95550 and PR107227 are actually resolved by this commit;
2. add execution test cases — the installed `pr93554.f90` is `dg-do compile`;
3. confirm later compiler passes handle the looser CFG correctly on the device.

This comment summarises the verification work and links to the artifacts
now committed under `pr/93554/`, `pr/95550/`, `pr/107227/`.  Nothing has
been posted to Bugzilla or gcc-patches yet.

### Duplicate status

| bug      | reporter         | form                                                | pre-fix | trunk   |
|----------|------------------|-----------------------------------------------------|---------|---------|
| 93554    | gscfq@t-online.de| derived type w/ allocatable component, `loop private`| ICE     | clean   |
| 95550    | Burnus           | `parallel create(A)` + `loop private(A)`            | ICE     | clean   |
| 95550    | Gribov           | `parallel loop private(GWORK)` on `complex(8)` alloc | ICE     | clean   |
| 107227   | Bryngelson       | `parallel loop private(arr)` on real alloc          | ICE     | clean   |

Every pre-fix back-trace ends at `omp-expand.cc:7722` inside
`expand_oacc_for`.  On trunk all four reproducers compile cleanly; see
the `dumps/` directories in each `pr/<n>/`.

### Execution test coverage (new)

Three draft tests staged under `pr/93554/tests/`, one per scenario:

- `pr93554-private-derived-alloc-component.f90`
- `pr107227-private-whole-allocatable.f90`
- `pr95550-parallel-create-private.f90`

Each exercises `!$acc parallel loop` with explicit `gang`, `worker`,
`vector` and `seq`, plus an `!$acc kernels` variant, and asserts result
correctness with `stop N`.

Matrix:

| scenario | host-fallback (-O0..-O3,-Os) | NVPTX sm_89 |
|----------|------------------------------|-------------|
| PR93554  | PASS (5 parallelism variants × 6 optimisation levels) | PASS |
| PR95550  | PASS                                                   | PASS |
| PR107227 | PASS                                                   | PASS |

Filtered PASS lines and the libgomp summary (6374 passes, 0 new
FAIL/XPASS) are in `pr/93554/verification/host-run.log`; offload output
is in `pr/93554/verification/nvptx-run.log`.

### Follow-on-pass correctness on the device

`GOMP_DEBUG=1` trace of the PR93554 test on NVPTX
(`pr/93554/verification/nvptx/gomp-debug-pr93554.log`) shows the
generated PTX:

- has `.entry` points for all five variants (gang/worker/vector/seq/kernels);
- contains explicit `call __nvptx_free` / `call __nvptx_malloc` instructions
  inside the device kernel — i.e. the finalisation path seen in the
  post-fix CFG is emitted into the device image, not dropped on the host.

`pr/93554/verification/cfg.md` documents the CFG comparison between
OpenACC and a matching OpenMP control case (`!$omp parallel do
private(x)`) and explains why the OpenMP path never tripped the
assertions: in OpenMP the finalisation sits between the for's
`omp_return` and the enclosing parallel's `omp_return`, outside the
loop; in OpenACC the loop directive *is* the construct, so the extra
blocks land between `cont_bb` and the region's single `omp_return`.

### Bounds of this verification

- Tests do not allocate the private entity inside the loop body, so the
  `__nvptx_free` branch is a no-op at runtime.  PTX is still emitted for
  it, which is what we wanted to verify.  A stricter test that *does*
  allocate inside the body would additionally exercise the `CHUNKS > 1`
  placement of finalisation — a pre-existing code-generation question
  unaffected by this commit; flagging as a potential follow-up.
- AMD GCN offload was not tested (NVPTX-only hardware here).

### Next steps (not yet done)

- Upstream submission of the execution tests, once Thomas is happy with
  the coverage.
- Closing PR95550 and PR107227 as DUPLICATE of 93554 on Bugzilla.
- Reply to Thomas on gcc-patches summarising the above.

All three are pending explicit go-ahead.
