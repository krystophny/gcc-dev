# Fortran Regression ROI Task List

Checked against `upstream/master` (`569ace1fa50`) on 2026-03-22.

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

- [x] Deep dive: reproduced on clean trunk, inspected the existing Bugzilla patch, and confirmed the failure in the parser cleanup path.
- [x] Meta docs: added `pr/84245/README.md`, reproducer, status, and submission packet files.
- [x] Clean fix: implemented the minimal trunk fix in `gfc_match_select_type`.
- [x] Critical review: checked the fix shape against the same rollback/error-recovery family as PR106946 / PR82721.
- [x] Full revision: rebuilt, validated the direct reproducer, ran `dg.exp=pr84245.f90`, and completed full `check-gfortran`.
- [x] Emit patch: committed, verified with `gcc-verify`, exported patch, and pushed `origin/pr84245-fix`.
- [x] Bugzilla: refreshed patch posted as attachment 63998 with the cleanup-path explanation and validation summary.

### T2: PR108382

- [x] Deep dive: reduced/reproduced the free-form continuation bug on clean trunk and isolated the stale opposite-flag transition in the scanner helpers.
- [x] Meta docs: added `pr/108382/README.md`, testcase, status, patch, and submission packet files.
- [x] Clean fix: reset only the necessary opposite directive flag on fresh free-form OpenACC/OpenMP directive starts.
- [x] Critical review: cross-checked against preserved negative mixed-continuation cases and the existing fixed-form behavior from `4facf2bf5b7`.
- [x] Full revision: direct reproducers, focused `goacc.exp` checks, broader `goacc.exp` coverage, and a fresh full `check-gfortran` rerun on `pr108382-fix` are clean.
- [x] Emit patch: branch `pr108382-fix`, commit `f738265ceff7bc2fa3ebcbaf0dc7d807e81d81a8`, exported patch, `gcc-verify`, pushed to fork.
- [x] Bugzilla: posted reviewed patch as attachment 63999 with the scanner-state explanation and validation summary.

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

`T1 / PR84245` and `T2 / PR108382` are complete through Bugzilla posting and
fresh full-suite reruns. The other active patch branches with Bugzilla-posted
patches, `PR95879` and `PR124512`, were also rerun clean through full
`check-gfortran` on 2026-03-22.

The next execution target is `T3 / PR85352 + PR96986`.

`T1` had the best effort-to-progress ratio because:

- there is already a candidate Bugzilla patch to validate,
- the failure is in a parser/error-recovery area where we already have recent fix experience,
- the likely fix scope is narrower than the mixed-directive and `ENTRY` tasks.
