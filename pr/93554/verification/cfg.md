# CFG inspection for PR93554 / PR95550 / PR107227

All observations are made against the `ompexp` pass dumps (the same pass
where `expand_oacc_for` runs).  Baseline f951 comes from the worktree at
`010618b8dcb^` (no fix applied); trunk f951 comes from the main gcc-build
(post-fix).  The baseline runs abort at `omp-expand.cc:7722` for all three
reproducers — that is precisely the second original assertion
`BRANCH_EDGE (entry_bb)->dest == exit_bb`.

Reference line in the pre-fix source (omp-expand.cc near line 7718):

```
  /* entry_bb has two sucessors; the branch edge is to the exit
     block,  fallthrough edge to body.  */
  gcc_assert (EDGE_COUNT (entry_bb->succs) == 2
              && BRANCH_EDGE (entry_bb)->dest == exit_bb);        /* <-- 7722 */
```

The second conjunct is what fails.  Fix replaces it with
`EDGE_COUNT == 2` only, keeps the edge-count invariants, and removes
the subsequent `FALLTHRU_EDGE(cont_bb)->dest == exit_bb` and
`EDGE_COUNT(exit_bb->preds) == 1 + (cont_bb != NULL)` checks.

## OpenACC region shape observed (post-expand_oacc_for)

Canonical pattern across all three reproducers
(`dumps/derived-alloc-component.f90.018t.ompexp`,
`dumps/parallel-create-private.f90.018t.ompexp`,
`dumps/parallel-loop-private.f90.018t.ompexp`):

```
entry_bb      -------------------.
   GIMPLE_OMP_FOR                |
   chunk_no = 0                  v
   chunk_max, step = .GOACC_LOOP (CHUNKS/STEP, ...)
            |
            v
       outer chunk header <----.
       .offset = .GOACC_LOOP (OFFSET, ...)
       .bound  = .GOACC_LOOP (BOUND,  ...)
       if (.offset < .bound) ----.
            |                    v
            |               body_bb  <-------------.
            |                 (iteration body)     |
            |                 .offset += .step     |
            |                 if (.offset < .bound)-'
            |
            v
       finalization_bb          (<-- inserted BB)
         if (priv.data != 0B) ---.
            |                    v
            |               free_bb
            |                 free (priv.data)
            |                 priv.data = 0B
            |                    |
            v                    v
       exit_bb  <---------------'
         GIMPLE_OMP_RETURN (chunk post, chunk_no increment elsewhere)
```

`entry_bb`, `cont_bb`, `exit_bb` are as reported by the OMP region tree
header of each dump, e.g. for the 93554 reproducer:

```
bb 2: gimple_omp_target
    bb 6: gimple_omp_for
    bb 7: GIMPLE_OMP_CONTINUE
    bb 10: GIMPLE_OMP_RETURN
```

At `expand_oacc_for` time — **before** the `.GOACC_LOOP`/CHUNKS scaffolding
is inserted — the CFG simplifies to:

```
entry_bb -> body_bb                              (FALLTHRU_EDGE)
entry_bb -> finalization_bb -> ... -> exit_bb    (BRANCH_EDGE)

body_bb  -> body_bb                              (back-edge)
cont_bb  -> body_bb                              (BRANCH_EDGE)
cont_bb  -> finalization_bb -> ... -> exit_bb    (FALLTHRU_EDGE)
```

The pre-fix assertions require:

- `BRANCH_EDGE(entry_bb)->dest == exit_bb`     — **fails**, now finalization_bb
- `FALLTHRU_EDGE(cont_bb)->dest  == exit_bb`    — **fails**, now finalization_bb
- `EDGE_COUNT(exit_bb->preds) == 1 + (cont_bb != NULL)` — **fails**, one
  more predecessor arrives from free_bb

The post-fix assertions require only:

- `EDGE_COUNT(entry_bb->succs) == 2`
- `EDGE_COUNT(cont_bb->succs)  == 2`
- structural `bed == body_bb || single_succ_edge(bed)->dest == body_bb`
  — **still checked**, and still holds (since the inserted finalization
  chain is off `entry_bb`'s branch edge, not `cont_bb`'s branch edge).

## OpenMP control case (PR93554 source, `!$omp parallel do private(x)`)

`dumps/omp-control.f90.018t.ompexp` — OMP region tree:

```
bb 11: gimple_omp_target
    bb 12: gimple_omp_parallel
        bb 16: gimple_omp_for
        bb 17: GIMPLE_OMP_CONTINUE
        bb 18: GIMPLE_OMP_RETURN         <-- for's omp_return
    bb 21: GIMPLE_OMP_RETURN             <-- parallel's omp_return
bb 22: GIMPLE_OMP_RETURN                 <-- target's omp_return
```

Finalization lives in bb 19 (`if (x.b.data != 0B)`) and bb 20 (`free`) —
**between** bb 18 and bb 21, i.e. inside the parallel region but **after**
the for's `omp_return`.  This is why OpenMP never tripped the equivalent
assertions: its `expand_omp_for` path sees the for's exit already
immediately followed by its own `GIMPLE_OMP_RETURN`; the finalization sits
outside the for and inside the parent parallel.

For OpenACC (PR93554 source, `!$acc loop private(x)`) the loop directive
*is* the construct; there is no surrounding `acc parallel`/`acc kernels`
OMP region separate from the loop's.  The finalization must land inside
the single region, which is what produces the shape documented above.

## What this proves and what it does not

Proved:

- The three scenarios share one CFG shape; the relaxation makes them all
  compile.  Execution dumps and ICE logs under
  `pr/<n>/dumps/baseline-*.log` confirm `expand_oacc_for:7722` is the
  sole site of failure on the pre-fix baseline.
- The one structural invariant the fix keeps
  (`bed == body_bb || single_succ_edge(bed)->dest == body_bb`) still
  holds; loop-body topology is preserved.

Not proved by inspection alone (kept for the execution-test phase):

- Correctness of later OMP/offload/back-end handling for the private
  variable on the device side.  The dump shows `free` is emitted inside
  the offloaded function; we have **not** checked that it runs on the
  device (vs. spuriously on the host) under NVPTX offload.
- Whether finalization runs once per thread or once per chunk under
  `CHUNKS > 1` — the chunk loop wraps the finalization in the emitted
  code, so a thread that services multiple chunks may execute the
  finalization repeatedly.  For the PR93554 reproducer this is a no-op
  at runtime because `x%b.data` is never non-null inside the body, so
  it does not affect the current regression test.  It is nonetheless a
  question worth revisiting for execution tests that *do* allocate the
  component inside the region.

Artifacts:

- `pr/93554/dumps/derived-alloc-component.f90.018t.ompexp` — trunk OpenACC.
- `pr/93554/dumps/omp-control.f90.018t.ompexp` — OpenMP reference.
- `pr/95550/dumps/parallel-create-private.f90.018t.ompexp` — trunk 95550
  (create + private variant).
- `pr/95550/dumps/parallel-loop-private.f90.018t.ompexp` — trunk 95550
  (parallel-loop variant).
- `pr/107227/dumps/parallel-loop-private.f90.018t.ompexp` — trunk 107227.
- `pr/93554/dumps/baseline-ice.log`,
  `pr/95550/dumps/baseline-{create,loop}-ice.log`,
  `pr/107227/dumps/baseline-ice.log` — pre-fix ICE output.
