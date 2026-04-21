# Provenance audit: OpenACC private-allocatable execution tests

All five tests staged for upstream submission
(`libgomp/testsuite/libgomp.oacc-fortran/pr93554-1.f90`, `-2.f90`,
`-3.f90`, `pr95550-1.f90`, `pr107227-1.f90`) were written in this
repository for the PR93554 verification cycle.  No lines were copied
from an existing upstream testcase.

A survey of `libgomp/testsuite/libgomp.oacc-fortran/` for tests that
combine an OpenACC `private(...)` clause with an allocatable
component or whole allocatable array returned no matches (see the
Explore agent report in `/home/ert/.claude/plans/concurrent-humming-firefly.md`,
findings 2 and 3).  The closest existing tests --
`kernels-private-vars-loop-gang-*.f90` (scalar privates) and
`acc-attach-detach-2.f90` (allocatable components via `acc_attach` /
`acc_detach`, not via `private`) -- were read and confirmed
structurally different.  They were not used as a starting point.

## Per-test lineage

| file                                      | source of design                                                                 |
|-------------------------------------------|----------------------------------------------------------------------------------|
| `pr93554-1.f90`                           | structure derived from the PR93554 reproducer (gscfq@t-online.de, 2020-01-30)     |
| `pr93554-2.f90` (NEW)                     | original for runtime-free-edge coverage; no external source                        |
| `pr93554-3.f90` (NEW)                     | original for per-gang independence coverage; no external source                    |
| `pr95550-1.f90`                           | structure derived from the PR95550 reproducers (Burnus 2020-06-05; Gribov 2021)    |
| `pr107227-1.f90`                          | structure derived from the PR107227 reproducer (Bryngelson, 2022-10-12)            |

Where a test's subject matter traces back to a Bugzilla reproducer we
used the reproducer only to identify the failing shape; the
execution-test program text (driver loop, `check(...)` pattern,
expected values) is our own.  No reproducer text is quoted verbatim.

## Cross-check against upstream test patterns

The DejaGnu directives (`! { dg-do run }`, one test program per file)
match the conventions of neighbouring tests
(`collapse-2.f90`, `allocatable-1-1.f90`, `attach-descriptor-1.f90`).
No `! { dg-options ... }` beyond the default is needed because the
tests rely on the libgomp harness's standard OpenACC compile flags
(`-fopenacc`, default optimisation matrix).
