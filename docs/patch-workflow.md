# Patch Workflow

## Bug Triage

Before writing any fix, verify the bug and record its status across branches.

### Step 0: Full Bugzilla context (MANDATORY)

Never start a fix from the summary line alone. Pull the complete bug
history first: reporters, maintainers, and prior patch attempts often
change the picture entirely:

```bash
scripts/gcc-bugzilla.sh info <n>
scripts/gcc-bugzilla.sh comments <n>
scripts/gcc-bugzilla.sh attachments <n>       # download if any look relevant
```

Distill the load-bearing facts (root-cause hints, duplicate PRs, failed
prior approaches, provenance of pasted reproducers) into a few lines of
`pr/<n>/README.md`. Do not paste Bugzilla content verbatim.

### Step 1: Verify on current trunk

```bash
# Build trunk (gcc-build/ should already track upstream/master)
cd gcc-build/gcc && make -j32

# Compile/run the reproducer from Bugzilla
gcc-build/gcc/gfortran -B gcc-build/gcc reproducer.f90 -o /tmp/test && /tmp/test
```

If the bug **no longer reproduces on trunk**, the fix was silently merged.
Proceed to Step 1b. Otherwise skip to Step 2.

### Step 1b: Bug already fixed: bisect and add test coverage

```bash
# Bisect the fixing commit
cd gcc && git bisect start upstream/master <last-known-bad-commit>
git bisect run ../scripts/bisect-test.sh reproducer.f90
```

Record the fixing commit in `pr/<number>/README.md`. Then write a testcase
(if none exists) to prevent regressions and submit it as a standalone patch:

```bash
# Add testcase only, no code fix needed
git checkout upstream/master && git checkout -b pr<number>-testcase
cp reproducer.f90 gcc/testsuite/gfortran.dg/pr<number>.f90
# Add DejaGnu directives, commit, verify, push
```

### Step 2: Check release branches

Test the reproducer on each active release branch to determine where the
regression exists. Record results in `pr/<number>/README.md`:

```bash
for branch in releases/gcc-15 releases/gcc-14 releases/gcc-13; do
  echo "=== $branch ==="
  # Use a dedicated build dir or the bisect build
  git -C gcc checkout $branch
  cd gcc-build && make -j32 2>&1 | tail -3
  cd gcc && gcc-build/gcc/gfortran -B gcc-build/gcc reproducer.f90 -o /tmp/test 2>&1
  /tmp/test 2>&1 || true
done
```

Update `pr/<number>/README.md` with:
```markdown
## Affected Versions
| Branch | Reproduces? | Notes |
|--------|-------------|-------|
| trunk (r16-NNNN) | yes/no | ... |
| releases/gcc-15 | yes/no | ... |
| releases/gcc-14 | yes/no | ... |
| releases/gcc-13 | yes/no | ... |
```

This table is required for later Bugzilla comments and backport decisions.

### Step 3: Fix development

Proceed to the patch creation steps below.

### Step 4: Final validation (MANDATORY before posting)

Every patch MUST pass ALL of the following test suites with zero failing
DejaGnu entries, except the documented local `bessel_6.f90` expected
failure in `docs/build-and-test.md`:

1. `scripts/check-fortran.sh`: Fortran frontend tests
2. `check-target-libgomp-fortran`: libgomp Fortran runtime harnesses

```bash
scripts/check-fortran.sh > /tmp/check-fortran.log 2>&1
grep -cE "^(FAIL|XPASS|UNRESOLVED|ERROR):" \
  gcc-build/gcc/testsuite/gfortran/gfortran.sum  # must be 0

cd gcc-build
make -j32 check-target-libgomp-fortran > /tmp/libgomp-fortran.log 2>&1
```

Partial passes are failure. Fix until zero new failures.

## Prerequisites (one-time setup in gcc/)

```bash
cd gcc

# Install GCC git aliases and prepare-commit-msg hook
bash contrib/gcc-git-customization.sh
# Answer: name, email, upstream=origin, account=ert, prefix=me, hook=yes

# Verify user.name is correct (not truncated)
git config user.name   # Must show "Christopher Albert"
git config user.email  # Must show "albert@tugraz.at"

# Required Python packages for mklog and gcc-verify
pip install --user --break-system-packages unidiff GitPython
```

## Creating patches

`lazy-fortran/gcc` (`origin`) is the public downstream fork. Its `master`
is the default branch and a verbatim mirror of upstream GCC `master`:
it is only ever fast-forwarded (`git push origin upstream/master:master`)
and never receives a fix. Each fix lives on its own branch with an open
pull request against `master`; that PR is the fix's review page and is
never merged. The former personal mirror `krystophny/gcc` is retired.
Exported patches live as `.patch` files in `pr/<number>/`.

```bash
# 1. Create the fix branch off origin/master in gcc/ (origin = lazy-fortran/gcc)
git -C gcc fetch origin upstream
git -C gcc checkout -b fix/pr<number>-<slug> origin/master

# 2. Make changes, rebuild, test
cd gcc-build/gcc && make -j32
../../scripts/check-fortran.sh dg.exp=pr<number>.f90
# The script regenerates gcc/site.exp and uses GCC's build-tree harness.

# 3. Stage changes
git -C gcc add gcc/fortran/changed-file.cc

# 4. Commit using gcc-commit-mklog (MANDATORY - auto-generates ChangeLog)
#    Write the commit message to a file first, then commit with -F.
#    The prepare-commit-msg hook appends the ChangeLog automatically.
#    The Assisted-by: line goes in the body, immediately above the
#    `\tPR <component>/<n>` line that begins the ChangeLog area;
#    gcc/contrib/gcc-changelog/git_commit.py rejects it as an
#    end-of-message trailer, so gcc-verify fails if it sits at the end.
#    No -s: an agent never adds Signed-off-by (step 7).
cat > /tmp/gcc-commit-msg.txt <<'MSG'
fortran: Short summary [PR<number>]

Description of the fix.

Assisted-by: Claude (Anthropic)
MSG
cd gcc && GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<number>"]' \
  git commit -F /tmp/gcc-commit-msg.txt

# 5. Verify the commit passes GCC checks (MANDATORY before push)
git gcc-verify HEAD

# 6. Push the branch and open a real PR against master immediately
#    (never a draft). PR title and body are the verified GCC commit
#    message; step 7 reuses them for the squashed export commit.
git -C gcc push origin fix/pr<number>-<slug>
gh pr create --repo lazy-fortran/gcc \
  --base master --head fix/pr<number>-<slug> \
  --title "$(git -C gcc log -1 --format=%s fix/pr<number>-<slug>)" \
  --body "$(git -C gcc log -1 --format=%b fix/pr<number>-<slug>)"

# 6a. The quick-read summary goes in the FIRST PR COMMENT, which also
#     links the fork issue (the body stays pure commit message):
gh pr comment <pr-url> --repo lazy-fortran/gcc --body \
  "PR fortran/<number>: <one-line symptom>. Bugzilla: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=<number>. Issue: #<fork-issue>. Tests: check-fortran + libgomp-fortran clean; new gfortran.dg/pr<number>.f90."

# 6b. Run the machine review (/code-review or the review workflow) right
#     away. Confirmed findings become further commits on the branch; if
#     the message changes, update the PR title/body to the new message.

# 7. Squash at export, before any Bugzilla submission. The branch keeps
#    its history; the squash happens on a throwaway branch.
git -C gcc fetch origin upstream
git -C gcc checkout -b export/pr<number> upstream/master
git -C gcc merge --squash fix/pr<number>-<slug>
gh pr view <pr-url> --repo lazy-fortran/gcc --json title,body \
  --jq '.title + "\n\n" + .body' > /tmp/gcc-commit-msg.txt
git -C gcc commit -F /tmp/gcc-commit-msg.txt
git -C gcc gcc-verify HEAD
#    Chris adds his own DCO sign-off; an agent never writes this line:
#      git -C gcc commit --amend -s --no-edit
git -C gcc format-patch -1 HEAD -o ../pr/<number>/
git -C gcc checkout master && git -C gcc branch -D export/pr<number>

# 7a. Eligibility (fewer than 15 changed non-testsuite lines, Assisted-by,
#     Signed-off-by), then the file-based dry run and upload. Add
#     --obsolete <id> when replacing an earlier attachment.
python3 scripts/gcc-workflow.py ai-eligibility \
  pr/<number>/0001-*.patch --expected-assistant 'Claude Opus 5.5 (Anthropic)'
scripts/gcc-bugzilla.sh submit <number> \
  --expected-assistant 'Claude Opus 5.5 (Anthropic)'
GCC_BUGZILLA_MANUAL_CONFIRM=1 scripts/gcc-bugzilla.sh submit <number> \
  --expected-assistant 'Claude Opus 5.5 (Anthropic)' --execute

# 7b. Fork-only fixes (not eligible) get the PR-link comment instead
#     (standing authorization, see docs/upstream-submission.md). Lead:
#     "Open for review, comments welcome: <URL>". Then what the patch
#     changes, what was tested, relation to prior patches on the bug, and
#     one plain line saying the work was AI-assisted. Max ~15 lines.
scripts/bugzilla-pr-notify.sh <number> https://github.com/lazy-fortran/gcc/pull/<N> /tmp/bz-<number>.txt            # dry run
scripts/bugzilla-pr-notify.sh <number> https://github.com/lazy-fortran/gcc/pull/<N> /tmp/bz-<number>.txt --execute  # post

# 8. Track the patch in the meta-repo (branch + PR, as for any meta change)
git add pr/<number>/
git commit -m "pr<number>: add patch"
```

### PR lifecycle

- **One real PR per fix, opened immediately, against `master`.** Never
  draft PRs, never merged.
- **Machine review runs right after opening**; confirmed findings become
  further commits on the fix branch.
- **PR title and body are the verified GCC commit message**, the single
  source for the squashed export commit (step 7). Keep them in sync
  with the code.
- **The quick-read summary is the first PR comment**, short and
  targeted: symptom, Bugzilla link, fork issue, test evidence.
- **The PR stays open until the fix is on upstream `master`**, whether
  our patch or another one. Then close the PR (not merge) and the fork
  issue, each with a comment naming the upstream commit, e.g.
  `r17-1234-gabcdef01234`.
- **Refreshing a branch onto newer upstream** is a rebase plus
  force-push of the fix branch and needs Chris's OK for that push
  (CLAUDE.md pre-push checklist, item 7). Usually unnecessary: the
  export (step 7) applies the branch's squashed diff onto current
  `upstream/master` and shows any conflict there.
- **Avoid stacking.** For a genuine dependency, branch B off A's branch
  and open PR B with base `fix/prA-<slug>` so it shows only B's delta.

**If `gcc-verify` rejects an incomplete hook-generated ChangeLog skeleton:**
- Keep the mklog hook enabled, but switch from plain `git commit -F ...` to an
  editor-driven commit (`git commit -e` with a template/editor script).
- Let the hook run, then replace the message with the fully completed
  ChangeLog text before the commit is finalized.
- Re-run `git gcc-verify HEAD` immediately.  Repeating `git commit -F ...`
  with a fully written ChangeLog can otherwise lead to duplicated hook output.

## Commit rules (HARD RULES)

- **Every exported patch is exactly one commit**, squashed at export
  (step 7). Fix branches may carry several commits. No multi-commit
  patches in `pr/<number>/`; older `pr/<n>/0001..0003*.patch` triples
  are legacy and get squashed when revisited. Two genuinely independent
  changes get two branches, two PRs and two `pr/<number>/` directories.
- **Always use `gcc-commit-mklog`** or the `GCC_FORCE_MKLOG=1` env var
  with the prepare-commit-msg hook. Never hand-write ChangeLog entries.
- **Always run `git gcc-verify`** on the branch head before pushing and on
  the squashed export commit before export.
- **Never add `Signed-off-by:` as an agent** (no `git commit -s`, no
  trailer in a PR body). GCC accepts the DCO only from a human; Chris
  signs the export commit himself, and `gcc-workflow.py ai-eligibility`
  refuses a patch without a sign-off.
- **`Assisted-by:` on the export commit.** The PR message, and therefore
  the squashed export commit, carries an `Assisted-by:` line naming the
  model, in the body above the `\tPR ...` line. That is GCC's "clearly
  marked" requirement for LLM-generated content. WIP commits need no tag.
- **Branches go off `origin/master`** (lazy-fortran/gcc, equal to
  upstream), not off other fix branches.
- **One fix per branch** (e.g., `fix/pr123949-init-se`), not stacked.
- **Nothing is ever merged into the fork's `master`.**

### AI policy

The `lazy-fortran/gcc` fork carries a repository-level AI policy as the
governing declaration (the `Assisted-by:` line on each exported patch is
the per-contribution marking GCC's AI policy requires):

- AI tools are permitted for research, analysis, bug discovery,
  implementation, testing, review, documentation, and maintenance.
- Contributions are judged on correctness, quality, licensing, provenance,
  test coverage, and maintainability, not on whether AI was used.
- Every contribution has a human contributor who understands the change and
  accepts responsibility for its correctness, licensing, and maintenance.
- Third-party material must be identified and licensed appropriately
  regardless of whether an AI tool was involved (see "Provenance review").
- Because the repo-level policy declares AI use globally, **fixes from this
  workflow must be treated as LLM-derived for upstream purposes**: under
  GCC's AI policy (https://gcc.gnu.org/ai-policy.html, 2026), legally
  significant ones (≈15+ lines) cannot be offered to upstream GCC as code
  contributions; sub-threshold fixes and testcases can, if clearly marked
  `Assisted-by:` (see `docs/upstream-submission.md`). The
  one-patch-per-PR layout, the upstream-shaped ChangeLog, and the
  Bugzilla-numbered PR titles exist precisely to keep every fix
  dissectable and independently reviewable.

## Fix development rules

### DO

1. **Start with the failing condition** - write it down before coding
2. **Minimal fix first** - most bugs are single-condition fixes
3. **Check at the right level** - tree-level bugs need tree-level checks
4. **Refine conditions** - make checks more precise, don't add bypass params
5. **Test with nvfortran** - it defines correct OpenACC behavior
6. **Add debug tracing when stuck** - fprintf in runtime reveals actual state
7. **Verify fix actually works** - rebuild, reinstall, test with real reproducer
8. **Question initial hypothesis** - first plausible explanation often wrong

### DON'T

1. **Add bypass parameters** - refine the condition instead
2. **Fix in middle-end** when issue is Fortran-specific
3. **Add new infrastructure** for single-condition fixes
4. **Trust POINTER_TYPE_P alone** - distinguish real POINTER from pass-by-ref
5. **Add contiguous unnecessarily** - it causes copies for assumed-shape
6. **Assume tree dumps tell the whole story** - runtime behavior may differ
7. **Skip runtime testing** - compile-time analysis misses refcount/state bugs
8. **Trust asymmetric enter/exit** - if enter does X, exit should undo X

## Provenance review

### Hard rules

- **Never copy verbatim. Not even tests.** Every testcase, reproducer,
  helper, and code fragment we add to `gcc/` must be our own expression.
  Rewrite from scratch: different variable names, different array
  shapes, different format strings, different surrounding structure.
  Only purely factual bug-trigger values (`INT_MAX`, kind boundaries,
  standards-defined constants) are safe to reuse in isolation.
- **Bugzilla reporters routinely paste third-party test-suite content
  verbatim** (Fujitsu CTS, NAG, commercial benchmark suites). A
  reproducer appearing in a Bugzilla comment does **not** license it
  for downstream redistribution. Before deriving any testcase from a
  Bugzilla-posted reproducer, trace its origin: look for file paths
  (e.g. `Fortran/NNNN/NNNN_NNNN.f08`), suite names, or distinctive
  idioms. If the content is from an external suite, treat it as
  provenance-sensitive upstream material and rewrite from scratch.
- **The public availability of a reproducer is not attribution.** An
  Apache-2.0, BSD, or proprietary reproducer does not become
  GPL-compatible just because someone pasted it into a public bug
  tracker. Attribution and license obligations stay with the
  redistributor (us, if we ship the derivative).
- **If you cannot rewrite cleanly, drop the testcase.** A bug with a
  correct code fix and no regression test is acceptable. A fix plus a
  license-unclear test is not.

### Process

- Provenance review is mandatory for every patch, testcase, reproducer, helper,
  imported snippet, and externally-inspired code fragment.
- During editing, keep asking where each non-trivial code fragment came from and
  whether it is safe to adapt or must be rewritten from scratch. The answer is
  never "keep verbatim".
- Treat Bugzilla reproducers, mailing-list examples, upstream tests, standards
  examples, blog posts, SARD/CWE examples, OpenMP/OpenACC examples, BLAS/LAPACK
  code, and copied helper code as provenance-sensitive by default.
- Before generating, exporting, or posting any patch, run from the repo root:
  `python3 scripts/check_testsuite_provenance.py --top 100 --json /tmp/provenance.json --no-fail-on-findings`
- The default run must still review any tests that are part of the local patch.
  Only the inherited historical testsuites are excluded by default. Pass
  `--include-testsuites` for an intentional whole-testsuite audit.
- After running the checker, manually review the findings relevant to the patch.
  This manual provenance review is required even if the checker output looks
  clean.
- The manual review must reconsider the source of reproducers and tests, proper
  attribution, whether verbatim copying is really necessary, and whether the
  license trail is compatible and locally clear.
- Do not add process-docs, audit markdown, or provenance bookkeeping noise to
  the working tree just to satisfy this rule.  Keep the codebase clean and add
  only the necessary license and attribution in source or adjacent license
  metadata where external code actually remains.
- Do not generate a patch until both the automatic checker and the manual
  provenance review are complete.

## PR directory structure

Each `pr/<number>/` contains:

```
pr/123280/
├── README.md           # Analysis, links, status
├── reproducer.f90      # Minimal test case
├── 0001-*.patch        # Exported patch
└── Makefile            # Optional multi-compiler testing
```

README.md header format:
```markdown
# Bug 123280: Short description

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123280
- **Issue:** https://github.com/lazy-fortran/gcc/issues/<n>
- **Fix PR:** https://github.com/lazy-fortran/gcc/pull/<n>

## Affected Versions
| Branch | Reproduces? | Notes |
|--------|-------------|-------|
| trunk (r16-NNNN) | yes/no | ... |
| releases/gcc-15 | yes/no | ... |
| releases/gcc-14 | yes/no | ... |
| releases/gcc-13 | yes/no | ... |
```

## Issue management (lazy-fortran/gcc)

User-facing bug tracking lives in `lazy-fortran/gcc` issues. Each tracked
GCC Bugzilla PR has one issue titled `PR<N>: <summary>` linking the
Bugzilla bug and, once it exists, the fix PR.

Issues use additive labels to track progress:

| Label | Meaning |
|-------|---------|
| `on-bugzilla` | The bug has a GCC Bugzilla report |
| `patch-wip` | Work-in-progress patch, not yet validated |
| `patch-ready` | Validated fix branch with an open PR on the fork |
| `has-upstream-patch` | The patch is attached on Bugzilla |
| `regression`, `wrong-code` | Classification, as on Bugzilla |
| (closed) | Fixed on upstream `master` |

An issue, like its fix PR, stays open until the fix is on upstream
`master`. Close both then, with a comment naming the upstream commit and
revision tag: `https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=<hash>`
(e.g. `r16-7700-ge0b70284cfa`). If Bugzilla is reopened after that,
reopen the issue.
