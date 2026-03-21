# Fortran Regression ROI Task List

Checked against `upstream/master` (`a60cf319b6c`) on 2026-03-21.

This list combines lowest expected effort with highest user-visible gain from
the current open regression set.  The goal is to keep tasks independent on top
of current upstream trunk whenever possible.

## Task Order

| Task | PRs | Why this cluster | Side effects / overlap | Independence on trunk |
|---|---|---|---|---|
| T1 | PR84245 | Lowest expected effort; parser/error-recovery ICE; candidate patch already exists on Bugzilla | Can affect the same cleanup paths as PR106946 and PR82721, but only positively if kept narrow | High |
| T2 | PR108382 | High user gain; valid mixed OpenACC/OpenMP code misparsed; likely localized flag/reset bug | May affect mixed directive continuation handling and nearby OpenACC/OpenMP parser cases such as PR102430 or PR93554 | High |
| T3 | PR85352 + PR96986 | Shared `ENTRY` semantic/diagnostic area; better handled as one task than two separate patches | Can interact with other `ENTRY` PRs, especially PR93814, PR95338, PR84779 | Medium |
| T4 | PR94978 | Low implementation risk; user-visible bogus warning on valid code | Can affect FE warning paths and PR90302-adjacent logic | High |

## Per-Task Execution Stages

Each task goes through the same stages:

1. Deep dive
2. Meta-doc update
3. Clean fix on top of current upstream master
4. Critical review
5. Full revision
6. Emit patch
7. Post patch on Bugzilla with a meaningful explanation

## Task Checklists

### T1: PR84245

- [ ] Deep dive: reproduce on clean trunk; inspect Bugzilla patch; confirm root cause in parser cleanup path.
- [ ] Meta docs: add `pr/84245/README.md`, reproducer, and status notes.
- [ ] Clean fix: implement the minimal trunk fix from first principles or refine the attached patch.
- [ ] Critical review: compare against PR106946 / PR82721 cleanup logic for unintended rollback interactions.
- [ ] Full revision: rebuild, targeted validation, and full `check-gfortran`.
- [ ] Emit patch: branch, commit, export patch, verify metadata.
- [ ] Bugzilla: post/refresh patch with an explanation of the exact broken cleanup path and why the fix is minimal.

### T2: PR108382

- [ ] Deep dive: reduce/reproduce the continuation-line parser bug on clean trunk and isolate the flag state transition.
- [ ] Meta docs: add `pr/108382/README.md`, testcase, and parser-state notes.
- [ ] Clean fix: reset only the necessary continuation/directive state on mixed OpenACC/OpenMP continuations.
- [ ] Critical review: cross-check against fixed-form and swapped-pragma variants.
- [ ] Full revision: targeted parser tests plus full `check-gfortran`.
- [ ] Emit patch: branch, commit, export patch, verify metadata.
- [ ] Bugzilla: post patch with a clear explanation of the mixed-directive continuation state machine.

### T3: PR85352 + PR96986

- [ ] Deep dive: reproduce both `ENTRY` diagnostics on clean trunk and map them to the same semantic decision points if possible.
- [ ] Meta docs: add `pr/85352/` and `pr/96986/` notes, plus one shared investigation summary.
- [ ] Clean fix: if both failures share a single rule, keep them in one patch; otherwise split cleanly into two minimal patches.
- [ ] Critical review: test against known `ENTRY` regressions and fixes, especially PR93814, PR95338, PR84779.
- [ ] Full revision: targeted `ENTRY` coverage plus full `check-gfortran`.
- [ ] Emit patch: branch or branches, commits, exported patches, verified metadata.
- [ ] Bugzilla: post explanation centered on the exact explicit-interface / spec-expression rule being enforced incorrectly.

### T4: PR94978

- [ ] Deep dive: reproduce warning on clean trunk and inspect `frontend-passes.c` / `do_subscript` behavior.
- [ ] Meta docs: add `pr/94978/README.md`, testcase, and warning-analysis notes.
- [ ] Clean fix: suppress only the false-positive path; do not weaken real out-of-bounds diagnostics.
- [ ] Critical review: check interaction with empty-loop and guarded-loop cases, and with PR90302-related logic.
- [ ] Full revision: targeted warning tests plus full `check-gfortran`.
- [ ] Emit patch: branch, commit, export patch, verify metadata.
- [ ] Bugzilla: post patch with an explanation of why the warning path is provably false on this loop structure.

## Current Execution Target

Start with `T1 / PR84245`.  It has the best effort-to-progress ratio because:

- there is already a candidate Bugzilla patch to validate,
- the failure is in a parser/error-recovery area where we already have recent fix experience,
- the likely fix scope is narrower than the mixed-directive and `ENTRY` tasks.
