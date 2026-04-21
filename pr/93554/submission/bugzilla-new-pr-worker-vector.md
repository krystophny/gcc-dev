# Draft new Bugzilla PR: worker/vector private allocatable wrong results on NVPTX

**Action:** file as new Bugzilla bug; cross-reference PR95397.

**Component:** middle-end (or fortran -- undecided; suggest
middle-end since the lowering path is shared and PR95397 is in
fortran).

**Summary:** `[OpenACC] Wrong results with 'gang worker vector'
partitioned 'private' of whole allocatable array on nvptx offload`

**Version:** 16.0.1 20260413 (experimental)

---

Using a whole allocatable array as a `private` entity on a
fully-partitioned `!$acc parallel loop gang worker vector` produces
wrong results on nvptx offload.  A structurally identical program
with a static (non-allocatable) array works correctly.

## Minimal reproducer (wrong results)

```fortran
program repro_wrong
  implicit none
  integer, parameter :: n = 256, m = 16
  integer :: res(n), j, k, bad
  integer, allocatable :: buf(:)
  allocate(buf(m))
  res = -1
  !$acc parallel loop gang worker vector private(buf) copy(res) &
  !$acc&              num_gangs(4) num_workers(4) vector_length(8)
  do j = 1, n
     do k = 1, m
        buf(k) = j*m + k
     end do
     res(j) = 0
     do k = 1, m
        res(j) = res(j) + buf(k)
     end do
  end do
  !$acc end parallel loop
  bad = 0
  do j = 1, n
     if (res(j) /= m*m*j + m*(m+1)/2) bad = bad + 1
  end do
  write(0,'(a,i0)') 'bad=', bad
end program
```

Output on nvptx offload (sm_89 JIT to RTX 5060 Ti, CUDA 13.2, GCC
16 trunk):

    bad=254

All iterations j >= 2 return `res(1)`'s value (392) instead of
`m*m*j + m*(m+1)/2`.  Iteration j = 1 is correct by coincidence
(its expected value equals the leaked value).

## Control (correct results)

Replacing the private entity with a static-sized array of the same
shape produces correct output:

```fortran
  integer :: buf(m)
```

leaves `bad = 0`.  The sole difference is the `private` entity
kind (whole allocatable vs static-sized local); lowering of the
former routes through the Fortran allocatable-private descriptor
machinery.

## Relationship to r16-8571 (PR93554)

The recent fix r16-8571-g010618b8dcb relaxes three
`gcc_assert` checks in `expand_oacc_for`, with no codegen change.
Pre-fix, the above reproducer ICE'd at `omp-expand.cc:7722`; post-
fix, it compiles and runs but returns wrong results.  This bug is
therefore a pre-existing codegen issue, not a regression from
r16-8571 -- r16-8571 only exposes it by letting the code through
to the back end.

## Relationship to PR95397

PR95397 (`[Fortran/OpenACC] Wrong results with 'loop vector'
inside 'routine'`) documents a different-shape but possibly same-
root-cause symptom: a block-local static array used with an inner
`!$acc loop vector` produces wrong results on nvptx.  Comment #4
(2024) adds a `loop worker private(B)` case with inner vector
loops.  The present report adds the allocatable-private shape on
a combined `gang worker vector` directive.  Triage should decide
whether to merge with PR95397 or treat as distinct.

## Build / run environment

- gfortran 16.0.1 20260413 (trunk, contains r16-8571)
- offload target nvptx-none, sm_89 PTX
- driver: NVIDIA 595.58.03, CUDA 13.2
- GPU: NVIDIA GeForce RTX 5060 Ti (Blackwell; sm_89 PTX is JIT'd
  on load)
- ACC_DEVICE_TYPE=nvidia

Host fallback (`-foffload=disable`) produces correct results, so
this is specific to the offload target.

## Workaround

Pin partitioning to `gang` only (or any subset excluding
`worker`/`vector`), or use a static-sized array instead of a
whole allocatable as the `private` entity.

## CC

Adding tschwinge (flagged the risk class for r16-8571) and
burnus (touched adjacent allocatable-private code).
