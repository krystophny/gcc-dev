# Bug 107227: ICE in expand_oacc_for — private whole allocatable array

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107227
- **Status:** NEW on Bugzilla; resolved on trunk by the PR93554 fix
  (`r16-8571-g010618b8dcb`).  Proposed disposition: DUPLICATE of 93554
  once a reviewer agrees.  Thomas Schwinge already noted this as a
  probable duplicate in 2022 (comment #1).
- **Meta-repo parent:** `pr/93554/`.

## Summary

Bryngelson (2022-10-12) reported an ICE compiling:

```fortran
program main
  integer :: i
  real, allocatable :: arr(:)
  allocate(arr(10))
  !$acc parallel loop private(arr)
  do i = 1, 10
    arr = 1.0
  end do
end
```

Back-trace ends at `expand_oacc_for`: same assertion, same emission
pattern as PR93554 and PR95550 — Fortran finalisation for the private
allocatable array inserts basic blocks between `cont_bb` and `exit_bb`.

## Reproducer

`repro/parallel-loop-private.f90` — Bryngelson's program verbatim.

## Before / after

- Pre-fix baseline: ICE at `omp-expand.cc:7722`.  See
  `dumps/baseline-ice.log`.
- Post-fix trunk: compiles cleanly.  See
  `dumps/parallel-loop-private.f90.018t.ompexp`.

## Execution

Covered by `pr/93554/tests/pr107227-private-whole-allocatable.f90`,
exercising `gang`, `worker`, `vector`, `seq` and a `kernels` variant
over a 32-element `real, allocatable :: arr(:)` that is explicitly
allocated and deallocated around each region.  Results:

- host-fallback (`-O0 .. -O3, -Os`): PASS.
- NVPTX device: PASS.

See `pr/93554/verification/host-run.log` and
`pr/93554/verification/nvptx-run.log`.
