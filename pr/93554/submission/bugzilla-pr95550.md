# Draft Bugzilla comment for PR95550

**Action:** post as new comment; propose RESOLVED DUPLICATE of PR93554.

---

Both the parallel-create-private shape (Burnus, comment #0) and the
parallel-loop-private-complex shape (Gribov, comment #1/2) reduce
to the same ICE site as PR93554.

- Pre-fix baseline (parent of 010618b8dcb): both reproducers ICE
  at omp-expand.cc:7722 (same assertion PR93554 trips).
- Post-fix (trunk, r16-8571-g010618b8dcb): both compile cleanly.
- ompexp pass dumps confirm the CFG shape matches PR93554's (same
  finalisation/free insertion, same entry_bb -> finalization_bb
  chain).

Execution coverage is staged in the pending follow-up patch at
libgomp/testsuite/libgomp.oacc-fortran/pr95550-1.f90, installing
Burnus's acc parallel create(A) + acc loop private(A) shape across
gang/worker/vector/seq/kernels parallelism variants.  PASS on host
fallback at six optimisation levels and on NVPTX sm_89.

Proposed disposition: RESOLVED DUPLICATE of PR93554.  The
execution test will land with the gcc-patches follow-up.
