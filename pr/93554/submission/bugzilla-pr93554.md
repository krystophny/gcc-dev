# Draft Bugzilla comment for PR93554

**Action:** post as new comment, then move status to RESOLVED FIXED.

**Attachment:** obsolete attachment 64138 (the already-merged v1 patch)
and attach the new `pr/93554/0002-libgomp-testsuite-OpenACC-Fortran-private-allocatabl.patch`
as "Follow-up: libgomp execution tests".

---

Follow-up per Thomas Schwinge's review of r16-8571 on gcc-patches
(<https://gcc.gnu.org/pipermail/gcc-patches/2026-April/713304.html>):

Five libgomp execution tests staged at
libgomp/testsuite/libgomp.oacc-fortran/:

- pr93554-1.f90  -- derived type with allocatable component, five
  parallelism variants (gang/worker/vector/seq/kernels).
- pr93554-2.f90  -- derived type with allocatable component
  allocated inside the loop body, gang-only; forces the
  per-thread finaliser __nvptx_free to run on the device.
- pr93554-3.f90  -- whole allocatable private under num_gangs(4)
  gang partitioning; exercises per-gang isolation + free edge.
- pr95550-1.f90  -- Burnus's acc parallel create(A) + loop
  private(A); verifies host-side A unchanged after region.
- pr107227-1.f90 -- Bryngelson's acc parallel loop private(arr)
  on a whole real allocatable.

All pass on host fallback at six optimisation levels and on NVPTX
sm_89.  GOMP_DEBUG=1 shows __nvptx_malloc and __nvptx_free inside
the offload entry body: for pr93554-2 the free runs at region exit
on every thread; for pr93554-3 it runs per gang.

Proposed disposition: RESOLVED FIXED, with PR95550 and PR107227
closed as DUPLICATE of this bug now that shared execution
coverage is in place.  Patch not yet posted to gcc-patches --
first round of on-list review comments will follow shortly.

Note: while validating the tests on NVPTX, I ran into a
pre-existing codegen issue for whole-allocatable privates under
gang+worker+vector partitioning on NVPTX (254/256 iterations
return iter-1's value; static-array variant works).  The fix
itself is pure assertion relaxation, so it cannot introduce this
miscompile -- r16-8571 only exposes it because the old ICE used
to block the offending shape at compile time.  Filed separately;
pr93554-2 and pr93554-3 therefore pin to gang-only partitioning.
