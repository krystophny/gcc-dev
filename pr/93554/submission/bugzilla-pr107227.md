# Draft Bugzilla comment for PR107227

**Action:** post as new comment; propose RESOLVED DUPLICATE of PR93554.

---

Confirming the duplicate-of-PR93554 status Thomas already flagged
in comment #1:

- Pre-fix baseline (parent of 010618b8dcb): the original
  reproducer (`real, allocatable :: arr(:)` with
  `!$acc parallel loop private(arr)`) ICEs at omp-expand.cc:7722
  -- same assertion PR93554 trips.
- Post-fix (trunk, r16-8571-g010618b8dcb): compiles cleanly; the
  ompexp pass dump shows the same finalisation-block CFG shape as
  PR93554.

Execution coverage is staged in the pending follow-up patch at
libgomp/testsuite/libgomp.oacc-fortran/pr107227-1.f90, installing
the whole-allocatable shape across gang/worker/vector/seq/kernels
parallelism variants.  PASS on host fallback at six optimisation
levels and on NVPTX sm_89.

Proposed disposition: RESOLVED DUPLICATE of PR93554.  The
execution test will land with the gcc-patches follow-up.
