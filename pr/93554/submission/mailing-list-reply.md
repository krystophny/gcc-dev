# Draft reply to Thomas Schwinge -- gcc-patches 2026-April/713304

Subject: Re: [PATCH,fortran] Fix Bug 93554 - [13/14/15/16 Regression] ICE in expand_oacc_for

In-Reply-To: 713304

---

Hi Thomas,

Thanks for the thorough review.  On all three asks:

(1) PR95550 and PR107227 duplicate status.

Both reduce to the same ICE site as PR93554 and are resolved by the
same commit.  I verified the whole-allocatable shapes from both
bugs: on the parent of 010618b8dcb both reproducers ICE at
omp-expand.cc:7722 (same assertion PR93554 trips), and on trunk both
compile cleanly.  Post-fix ompexp dumps confirm the CFG shape is
identical to PR93554's: same finalisation/free insertion, same
entry_bb -> finalization_bb -> exit_bb chain and cont_bb ->
finalization_bb fallthrough.

So: close as DUPLICATE of PR93554 on Bugzilla.  Test cases should
be installed -- the attached patch does that under libgomp rather
than gcc/testsuite, since the original bugs are runtime-behaviour
regressions, not just compile-time ICEs.

(2) Execution tests.

Attached patch adds five tests under libgomp/testsuite/
libgomp.oacc-fortran/:

  pr93554-1.f90   Derived type with allocatable component, five
                  parallelism variants (gang/worker/vector/seq/
                  kernels).  Canonical shape.
  pr93554-2.f90   Same derived type, allocatable component allocated
                  inside the loop body, gang-only partitioning.
                  Forces the per-thread finaliser __nvptx_free to
                  run at region exit (priv.b is non-null on exit).
                  A sentinel check at iteration start catches leaked
                  private storage.
  pr93554-3.f90   Whole allocatable private on num_gangs(4) gang
                  loop; double-phase write + sum exercises per-gang
                  isolation.
  pr95550-1.f90   Burnus's acc parallel create(A) + acc loop
                  private(A) shape; five parallelism variants.
  pr107227-1.f90  Bryngelson's whole-allocatable acc parallel loop
                  private(arr) shape; five parallelism variants.

dg-prune-output directives suppress the pre-existing
"using vector_length(32), ignoring 1" info diagnostic on the
low-parallelism variants so check-target-libgomp-fortran stays
green on nvptx.

(3) Extent of verification.

Host fallback (trunk gfortran, foffload=disable): 30 runs per
invocation = 5 scenarios x 6 optimisation levels (-O0 -O1 -O2 -O3
-Os -Og); all PASS, all numerics correct.

NVPTX offload (trunk offload compiler, sm_89 PTX target, NVIDIA RTX
5060 Ti Blackwell, CUDA 13.2, driver 595.58.03): all five PASS at
-O2 with ACC_DEVICE_TYPE=nvidia.

check-target-libgomp-fortran with the five tests added to
libgomp/testsuite/libgomp.oacc-fortran/: 60 new PASS, 0 new FAIL,
0 XPASS; suite totals 6398 expected passes vs 6374 baseline,
matching the +24 entry rows * 2 check types = +48 "expected
passes" counter offset plus 12 unsupported-but-counted lines.  0
UNRESOLVED.

CFG-level evidence (static inspection of ompexp dump, post-fix):

  entry_bb --(fallthru)-> body_bb
  entry_bb --(branch)--> finalization_bb --(guard)--> free_bb --> exit_bb
                                                  \_-> exit_bb
  cont_bb  --(branch)--> body_bb
  cont_bb  --(fallthru)-> finalization_bb (same chain as above)

The relaxed assertions are satisfied exactly as expected:
EDGE_COUNT(entry_bb->succs) == 2 and EDGE_COUNT(cont_bb->succs) ==
2 hold; the dropped equality to exit_bb was the only hazard and
its removal matches the shape the Fortran front end now emits.

Device-side correctness of later passes.  Here is the load-bearing
evidence for your concern about the "more loose" basic-block
layout on offload:

- PTX emission.  GOMP_DEBUG=1 traces for pr93554-2 and pr93554-3
  (NVPTX sm_89, offload trunk) show __nvptx_malloc / __nvptx_free
  call sites inside the .entry MAIN__$_omp_fn$0 body, not only in
  external runtime helpers:

      test                                 entries  malloc  free
      pr93554-1 (gated, baseline shape)       5       5       5
      pr93554-2 (alloc-in-body, NEW)          1       2       1
      pr93554-3 (private-independence, NEW)   1       1       1

  The five entries in pr93554-1 are its five parallelism variants;
  each reaches the free call but gates it with a guard that is
  always false at runtime because priv.b stays null throughout.
  pr93554-2 deliberately exits with priv.b non-null, so the free
  runs on every thread at region exit.  pr93554-3 carries a whole
  allocatable through num_gangs(4); the OpenACC runtime
  materialises the per-gang private copy on entry, and the free
  runs per gang at exit.

- Runtime correctness.  pr93554-2's sentinel check exits with
  stop 3 if a per-iteration private leaks state from a prior
  iteration; no such exit is observed across 128 iterations x 4
  gangs on nvptx.  pr93554-3's double-phase write/sum is sensitive
  to any thread interleaving that aliases the per-gang buf; the
  observed sum matches 2*m*(m*j + (m+1)/2) for every j in 1..n.

- Opt-level sweep.  All five tests PASS at -O0 -O1 -O2 -O3 -Os -Og
  on host fallback.  No optimisation-dependent failure.

Bounds of this verification (worth being explicit about):

- AMD GCN offload is not tested (local hardware is NVPTX-only).
  I can ship the patch without GCN coverage or wait for someone
  with GCN to run it; your call.
- The nvptx matrix is sm_89 PTX JIT'd to Blackwell.  The fix is
  architecturally neutral at the GCC level, so multi-sm_XX
  coverage is not load-bearing for this review.
- Fully-partitioned gang+worker+vector private for aggregate types
  on NVPTX exposes a separate, pre-existing codegen issue that
  r16-8571 only indirectly exposes (pre-fix the code ICE'd; post-
  fix it runs but returns wrong results for a whole-allocatable
  private).  Minimal reproducer:

    integer, allocatable :: buf(:)
    allocate(buf(16))
    !$acc parallel loop gang worker vector private(buf) num_gangs(4)
    do j = 1, 256
      do k = 1, 16; buf(k) = j*16 + k; end do
      res(j) = 0
      do k = 1, 16; res(j) = res(j) + buf(k); end do
    end do

  On trunk nvptx sm_89 this returns j=1's value for every j >= 2
  (254/256 wrong).  The static-array variant (integer :: buf(16))
  returns correct values, which confines the issue to the
  allocatable private materialisation, not the relaxed CFG.
  Possibly the same root cause as PR95397.  I will file it as a
  separate PR rather than conflate with this thread; pr93554-2
  and pr93554-3 therefore pin to gang-only partitioning.

Please let me know if you would like the patch restructured (for
example, splitting the five tests into per-PR commits) or if there
is a specific additional data-type or parallelism combination
worth covering before installation.

Full artefact bundle (CFG analysis, GOMP_DEBUG traces, per-entry
PTX call-site scan, libgomp.sum excerpt, per-test provenance audit)
is available on the meta-repo branch at
https://github.com/krystophny/gcc-dev/tree/main/pr/93554/verification .

Thanks,

Chris
