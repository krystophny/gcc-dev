# Bug 93554: ICE in expand_oacc_for with private derived type

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93554
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/62

## Root Cause

When a derived type with an allocatable component is used with the
private clause on an OpenACC loop, finalization code inserts additional
basic blocks between loop entry/continuation and exit blocks, violating
strict CFG assertions in expand_oacc_for.

## Fix

Relax the assertions to only verify edge count (two successors) without
requiring specific destinations. Based on Tobias Burnus' draft patch.

File: gcc/omp-expand.cc (expand_oacc_for)
