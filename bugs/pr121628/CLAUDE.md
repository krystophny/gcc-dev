# CLAUDE.md

Primary guidance for this repository now lives in `ALLOCATABLE_DEEPCOPY_PLAYBOOK.md`. Review that playbook before making changes; it contains the standards baseline, reproducer details, source deep dive, fix strategy, and verification checklist.

Key reminders when acting here:
- Honour the Fortran 2018+ allocatable assignment semantics—no shallow copies of nested allocatables.
- Work from the project root `/home/ert/code/gcc-dev/bugs`, using the Makefile targets and custom gfortran described in the playbook.
- Treat Intel ifx runs as the behavioural reference.
- Do not duplicate or resurrect the retired markdown summaries; keep the playbook authoritative and current.
