# Draft reply to Thomas Schwinge -- gcc-patches 2026-April/713304

Subject: Re: [PATCH,fortran] Fix Bug 93554 - [13/14/15/16 Regression] ICE in expand_oacc_for

In-Reply-To: 713304

---

Hi Thomas,

Thanks for the review.

Scope note: this follow-up adds only tests; no further source changes
beyond r16-8571.  And since LLM use on gcc-patches has sparked some
controversy, disclosure: I use Claude and GPT models while preparing
patches and flag that with an "Assisted-by: Claude (Anthropic)"
trailer, which this patch carries alongside my Signed-off-by.

On your three asks:

(1) PR95550 / PR107227 duplicate status.

Both reduce to the same assertion (omp-expand.cc:7722) as PR93554 and
are resolved by r16-8571-g010618b8dcb.  On the parent both reproducers
ICE; on trunk both compile cleanly and the post-fix ompexp CFG matches
PR93554's.  Close as DUPLICATE.  I've installed their test cases under
libgomp (attached) rather than gcc/testsuite because the originals are
runtime-behaviour reports, not compile-time ICEs.  Duplicate-of
comments posted on the two bugs:
  https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95550
  https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107227
and the follow-up is attached as patch 64265 on the parent bug:
  https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93554

(2) Execution tests.

Attached patch adds five tests under
libgomp/testsuite/libgomp.oacc-fortran/:

  pr93554-1.f90   Canonical derived-type-with-allocatable-component
                  shape; five parallelism variants.
  pr93554-2.f90   Allocation inside the loop body, gang-only; forces
                  __nvptx_free at region exit.  Sentinel check
                  detects leaked private storage.
  pr93554-3.f90   Whole allocatable private, num_gangs(4); double-
                  phase write+sum checks per-gang isolation.
  pr95550-1.f90   Burnus's create(A) + loop private(A); five variants.
  pr107227-1.f90  Bryngelson's whole-allocatable private; five
                  variants.

dg-prune-output suppresses the pre-existing
"using vector_length(32), ignoring 1" info diagnostic.

(3) Extent of verification.

- Host fallback (trunk gfortran -foffload=disable): 5 scenarios x 6
  opt levels (-O0..-O3 -Os -Og), all PASS.
- NVPTX offload (trunk, sm_89 / RTX 5060 Ti, CUDA 13.2): all five
  PASS at -O2 with ACC_DEVICE_TYPE=nvidia.
- check-target-libgomp-fortran: +60 PASS, 0 FAIL/XPASS/UNRESOLVED
  over the 6374-pass baseline.
- GOMP_DEBUG=1 PTX trace shows __nvptx_malloc/__nvptx_free call
  sites inside the .entry body for pr93554-2/3, not only in runtime
  helpers.  pr93554-2's sentinel and pr93554-3's sum identity hold
  across all iterations.

Bounds worth noting:

- AMD GCN untested (NVPTX-only hardware).
- Fully-partitioned gang+worker+vector with an aggregate private
  exposes a separate codegen bug on NVPTX that r16-8571 only
  uncovers (wrong results for whole-allocatable private; static-
  array variant is fine).  Filed as PR124964, cross-linked with
  PR95397 which may share the same root cause:
    https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124964
  pr93554-2/3 therefore pin to gang-only.

Full artefact bundle (CFG analysis, GOMP_DEBUG traces, PTX call-site
scan, libgomp.sum excerpt, per-test provenance audit) is at
https://github.com/krystophny/gcc-dev/tree/main/pr/93554/verification .

Thanks,

Chris
