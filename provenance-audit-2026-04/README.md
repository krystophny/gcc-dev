# Bugzilla-provenance attribution audit — 2026-04-22

Retrospective attribution-header additions for 27 Fortran testcases
re-using Bugzilla Comment #0 reducers (4 of them Fujitsu-CTS
derivatives).  Audit covers meta-repo issues #139–#165 on
`krystophny/gcc-dev`.

Each patch adds one (or, for Fujitsu-derived reducers, two) comment
lines to a test file.  No behavioural change.  Attribution is not
strictly required for small Bugzilla reducers — GCC testsuite
convention is inconsistent — but we are adding it retroactively for
provenance safety and completeness.

## Patch groups

**Group A1** — tests already in `upstream/master` via an Albert commit
(18 issues, 17 patches since #149 + #150 share a file pair).
Distribution: patch series on top of `upstream/master`.

**Group A2** — tests already in `upstream/master` via another maintainer's
commit (6 issues).  Distribution: same patch series; the patches will
not be sent without the original committer's OK (recorded as a
Bugzilla follow-up note per issue).

**Group B** — `pr103276.f90` currently lives only on Bugzilla attachment
63134 and fork branch `origin/openacc`; not in `upstream/master`.
Distribution: one patch that adds the attributed testcase on top of
`upstream/master`; intended to obsolete attachment 63134 once the
companion `trans-openmp.cc` change is rebased onto current trunk (the
cherry-pick conflict was non-trivial so the frontend portion is NOT
included here — it stays at commit `0bb84432a01` on `origin/openacc`
pending rebase).

**Group C** — three files that live only on fork branches, never
published externally.  Header edits on the respective branches;
patches kept here for reference.

## Layout

```
provenance-audit-2026-04/
└── 0000-cover-letter.patch          # series cover letter (Groups A1+A2)

pr/<N>/attribution/
└── 0NNN-testsuite-Add-Bugzilla-reporter-attribution-*.patch
```

For branch `testsuite/contributed-by-audit-2026-04` (Group A1+A2, 23
patches + cover, branched off `upstream/master`) see the gcc checkout;
the `0NNN-*.patch` numbering in each `pr/<N>/attribution/` directory
matches the series order.

Group B: `pr/103276/attribution/0001-testsuite-Add-attributed-pr103276.f90-testcase-PR-fo.patch`
on branch `testsuite/pr103276-with-attribution`.

Group C fork-only patches live on the respective fork branches
(`pr124631-fix`, `pr124666-fix`, `pr121472-constructor-finalizer-ice`)
and are also copied into each `pr/<N>/attribution/` directory.

## Commit trailers (every patch)

```
Assisted-by: Claude (Anthropic)
Assisted-by: GPT (OpenAI)
Signed-off-by: Christopher Albert <albert@tugraz.at>
```

`Assisted-by:` lines sit before the ChangeLog block — GCC's
`contrib/gcc-changelog/git_commit.py` only recognises a fixed set of
trailer prefixes (signed-off-by, reviewed-by, tested-by, acked-by,
suggested-by, reported-by, co-authored-by), so non-standard `Assisted-by:`
must live in the description area to avoid `git gcc-verify` failures.

## Delivery status

No patch has been posted to `gcc-patches@gcc.gnu.org`, `fortran@gcc.gnu.org`,
or Bugzilla.  Files are on-disk only, in this meta-repo, awaiting user
approval.

## Issues updated

Meta-repo issues #139–#165 were rewritten to record the distribution
status and the per-file delivery path for each case; see
`/home/ert/.claude/plans/floofy-honking-pike.md` for the full plan.
