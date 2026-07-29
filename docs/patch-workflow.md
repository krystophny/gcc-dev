# Patch Workflow

## Bug Triage

Before writing any fix, verify the bug and record its status across branches.

### Step 1: Verify on current trunk

```bash
# Build trunk (gcc-build/ should already track upstream/master)
cd gcc-build/gcc && make -j32

# Compile/run the reproducer from Bugzilla
gcc-build/gcc/gfortran -B gcc-build/gcc reproducer.f90 -o /tmp/test && /tmp/test
```

If the bug **no longer reproduces on trunk**, the fix was silently merged.
Proceed to Step 1b. Otherwise skip to Step 2.

### Step 1b: Bug already fixed — bisect and add test coverage

```bash
# Bisect the fixing commit
cd gcc && git bisect start upstream/master <last-known-bad-commit>
git bisect run ../scripts/bisect-test.sh reproducer.f90
```

Record the fixing commit in `pr/<number>/README.md`. Then write a testcase
(if none exists) to prevent regressions and submit it as a standalone patch:

```bash
# Add testcase only — no code fix needed
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

1. `scripts/check-fortran.sh` — Fortran frontend tests
2. `check-target-libgomp-fortran` — libgomp Fortran runtime harnesses

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

```bash
# 1. Create branch off origin/main in gcc/ (origin = lazy-fortran/gcc;
#    falls back to upstream/master until the fork exists)
git -C gcc fetch origin
git -C gcc checkout -b fix/pr<number>-<slug> origin/main

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
#    `\tPR <component>/<n>` line that begins the ChangeLog area —
#    gcc/contrib/gcc-changelog/git_commit.py rejects it as an
#    end-of-message trailer, so gcc-verify fails if it sits at the end.
cat > /tmp/gcc-commit-msg.txt <<'EOF'
fortran: Short summary [PR<number>]

Description of the fix.

Assisted-by: Claude (Anthropic)
EOF
cd gcc && GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<number>"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt

# 5. Verify commit passes GCC checks (MANDATORY before push)
git gcc-verify HEAD

# 5b. Re-check the Signed-off-by trailer explicitly.  gcc-verify does not
#     enforce its presence, and an editor/template-based commit or a
#     hook-driven message rewrite can silently drop it.
msg=$(git log -1 --format=%B)
echo "$msg" | grep -q '^Signed-off-by: ' \
  || { echo "ERROR: missing Signed-off-by trailer in commit"; exit 1; }

# 6. Push the branch to the downstream fork and open the PR
git -C gcc push origin fix/pr<number>-<slug>
gh pr create --repo lazy-fortran/gcc \
  --base main --head fix/pr<number>-<slug> \
  --title "PR<number>: <summary>" \
  --body "Upstream: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=<number>"

# 6b. Machine review before merge: run /code-review (or the repo's review
#     workflow) against the PR.  Address confirmed findings, then
#     squash-merge so lazy/main gets exactly one commit for this fix.
gh pr merge --repo lazy-fortran/gcc --squash <pr-url>

# 7. Export the squashed commit and track it in the meta-repo
git -C gcc fetch origin
git -C gcc format-patch -1 origin/main -o ../pr/<number>/
patch=$(ls -t pr/<number>/0001-*.patch | head -n1)
grep -q '^Signed-off-by: ' "$patch" \
  || { echo "ERROR: exported patch missing Signed-off-by trailer"; exit 1; }
git add pr/<number>/
git commit -m "pr<number>: add patch"
git push origin main

# 8. Delete the local fix branch once merged and exported
git -C gcc checkout master
git -C gcc branch -D fix/pr<number>-<slug>
```

`lazy-fortran/gcc` (`origin`) is the public downstream fork; its `main` is
official GCC master plus squash-merged Lazy Fortran fixes, one commit per
Bugzilla PR. The former personal mirror `krystophny/gcc` is retired.
Patch bodies additionally live as `.patch` files in `pr/<number>/`.

**If `gcc-verify` rejects an incomplete hook-generated ChangeLog skeleton:**
- Keep the mklog hook enabled, but switch from plain `git commit -F ...` to an
  editor-driven commit (`git commit -e` with a template/editor script).
- Let the hook run, then replace the message with the fully completed
  ChangeLog text before the commit is finalized.
- Re-run `git gcc-verify HEAD` immediately.  Repeating `git commit -F ...`
  with a fully written ChangeLog can otherwise lead to duplicated hook output.
- After any editor/template-based commit, explicitly re-check that the
  `Signed-off-by:` trailer is still present.  A full-message replacement can
  silently drop the `-s` trailer even when `git commit -s` was used.

## Commit rules (HARD RULES)

- **Every patch is exactly one commit.** Squash any work-in-progress or
  staged sub-commits before `git format-patch`.  No multi-commit
  patches in `pr/<number>/`, no `0001-..., 0002-..., 0003-...` series
  for a single PR.  If two changes are genuinely independent, they get
  two PRs and two `pr/<number>/` directories — one commit each.  This
  is the rule going forward; older `pr/<n>/0001..0003*.patch` triples
  are legacy and get squashed when revisited.
- **Always use `gcc-commit-mklog`** or the `GCC_FORCE_MKLOG=1` env var
  with the prepare-commit-msg hook. Never hand-write ChangeLog entries.
- **Always run `git gcc-verify HEAD`** before pushing. It checks
  ChangeLog format, PR references, and other GCC conventions.
- **Always use `-s`** (Signed-off-by) on commits, and verify it survives in
  both the final commit message and the exported patch — `git gcc-verify`
  does not check it.
- **`Assisted-by:` on the final squashed commit only.** The squash-merge
  commit (equivalently the exported patch) carries an `Assisted-by:` line
  naming the model, in the body above the `\tPR ...` line. WIP commits on
  the PR branch need no tag. This is forward-compatibility: if GCC
  loosens its AI policy, every exported patch already satisfies the
  upstream "clearly marked" requirement. The repo-wide AI policy (below)
  remains the governing declaration.
- **Branches go off `origin/main`** (lazy-fortran/gcc), not off other fix
  branches.
- **One fix per branch** (e.g., `fix/pr123949-init-se`), not stacked.
- **Squash-merge PRs on lazy-fortran/gcc** so `main` gets exactly one
  upstream-shaped commit per Bugzilla PR, and only after a machine review
  of the PR.

### AI policy

The `lazy-fortran/gcc` fork carries a repository-level AI policy as the
governing declaration (per-commit `Assisted-by:` lines on squashed fix
commits are additional attribution, kept for upstream forward
compatibility):

- AI tools are permitted for research, analysis, bug discovery,
  implementation, testing, review, documentation, and maintenance.
- Contributions are judged on correctness, quality, licensing, provenance,
  test coverage, and maintainability — not on whether AI was used.
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
  one-commit-per-PR layout, the upstream-shaped ChangeLog, and the
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
  redistributor — us, if we ship the derivative.
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
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/12
- **Status:** PENDING (patch on fork) | MERGED (gcc commit abc123)

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
Bugzilla bug. Issues previously lived in `krystophny/gcc-dev`; migrate any
remainder with `scripts/migrate-issues.sh` (creates the issue in the fork
with labels, cross-links both, and closes the source issue).

Issues use additive labels to track progress:

| Label | Meaning |
|-------|---------|
| `patch-ready` | Working fix branch / open PR on the fork |
| `analysis-on-bugzilla` | Bug report/analysis posted to GCC Bugzilla |
| (closed) | Fix squash-merged into `main`, or fixed upstream |

### When adding labels, always include a comment with links:

- **analysis-on-bugzilla**: link to the Bugzilla bug
  `https://gcc.gnu.org/bugzilla/show_bug.cgi?id=<number>`

### When closing issues, always include:

- The squash-merge commit on `main` (fixed downstream), and/or
- the upstream commit and revision tag if GCC fixed it independently:
  `https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=<hash>` (e.g.,
  `r16-7700-ge0b70284cfa`)
