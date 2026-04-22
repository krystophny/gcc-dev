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

Every patch MUST pass ALL of the following test suites with zero new
FAIL/XPASS entries compared to baseline:

1. `check-gfortran` — Fortran frontend + gomp/goacc/goacc-gomp directories
2. `check-target-libgomp-fortran` — libgomp Fortran runtime harnesses

```bash
cd gcc-build/gcc
make -j32 -k check-gfortran > /tmp/check-gfortran.log 2>&1
grep -cE "^FAIL|^XPASS" testsuite/gfortran/gfortran.sum  # must be 0 new

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
# 1. Create branch off upstream/master in gcc/
git -C gcc checkout upstream/master
git -C gcc checkout -b pr<number>-fix

# 2. Make changes, rebuild, test
cd gcc-build/gcc && make -j32
make check-gfortran RUNTESTFLAGS="dg.exp=pr<number>.f90"

# 3. Stage changes
git -C gcc add gcc/fortran/changed-file.cc

# 4. Commit using gcc-commit-mklog (MANDATORY - auto-generates ChangeLog)
#    Write the commit message to a file first, then commit with -F.
#    The prepare-commit-msg hook appends the ChangeLog automatically.
#    Always include an Assisted-by: trailer naming the model used
#    (e.g. "Assisted-by: Claude (Anthropic)" or "Assisted-by: GPT-5 (OpenAI)").
cat > /tmp/gcc-commit-msg.txt <<'EOF'
fortran: Short summary [PR<number>]

Description of the fix.

Assisted-by: Claude (Anthropic)
EOF
cd gcc && GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<number>"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt

# 5. Verify commit passes GCC checks (MANDATORY before push)
git gcc-verify HEAD

# 5b. gcc-verify does NOT check trailers.  Check the final commit message
#     explicitly, especially after editor/template-based commits or any
#     hook-driven message rewrite.  Both Signed-off-by and Assisted-by
#     must be present.
msg=$(git log -1 --format=%B)
echo "$msg" | grep -q '^Signed-off-by: ' \
  || { echo "ERROR: missing Signed-off-by trailer in commit"; exit 1; }
echo "$msg" | grep -q '^Assisted-by: ' \
  || { echo "ERROR: missing Assisted-by trailer in commit"; exit 1; }

# 6. Export patch
git format-patch -1 HEAD -o ../pr/<number>/

# 6b. Verify the exported patch still contains both trailers.
patch=$(ls -t ../pr/<number>/0001-*.patch | head -n1)
grep -q '^Signed-off-by: ' "$patch" \
  || { echo "ERROR: exported patch missing Signed-off-by trailer"; exit 1; }
grep -q '^Assisted-by: ' "$patch" \
  || { echo "ERROR: exported patch missing Assisted-by trailer"; exit 1; }

# 7. Track in meta-repo (no push to fork)
cd .. && git add pr/<number>/
git commit -m "pr<number>: add patch"
git push origin main

# 8. Delete the local branch once the patch file is in pr/<number>/
git -C gcc checkout master
git -C gcc branch -D pr<number>-fix
```

The fork (`origin` in `gcc/`) carries only `master`. Patch bodies live as
`.patch` files in `pr/<number>/`; no persistent `pr*-fix` branches on the
fork, so there's nothing to push there.

**If `gcc-verify` rejects an incomplete hook-generated ChangeLog skeleton:**
- Keep the mklog hook enabled, but switch from plain `git commit -F ...` to an
  editor-driven commit (`git commit -e` with a template/editor script).
- Let the hook run, then replace the message with the fully completed
  ChangeLog text before the commit is finalized.
- Re-run `git gcc-verify HEAD` immediately.  Repeating `git commit -F ...`
  with a fully written ChangeLog can otherwise lead to duplicated hook output.
- After any editor/template-based commit, explicitly re-check that both the
  `Signed-off-by:` and `Assisted-by:` trailers are still present.  A
  full-message replacement can silently drop the `-s` trailer even when
  `git commit -s` was used, and the hook can likewise drop `Assisted-by`.

## Commit rules (HARD RULES)

- **Always use `gcc-commit-mklog`** or the `GCC_FORCE_MKLOG=1` env var
  with the prepare-commit-msg hook. Never hand-write ChangeLog entries.
- **Always run `git gcc-verify HEAD`** before pushing. It checks
  ChangeLog format, PR references, and other GCC conventions.
- **Always use `-s`** (Signed-off-by) on commits.
- **Always add an `Assisted-by:` trailer** naming the model used
  (e.g. `Assisted-by: Claude (Anthropic)`, `Assisted-by: GPT-5 (OpenAI)`).
  This is mandatory for every commit on every patch branch, with no
  exceptions.  Disclosure is the rule, not a judgment call about how much
  the model contributed.  The existing no-tool-tag rule applies to
  subjects, branch names, PR titles, and issue titles only; trailers are
  explicitly allowed and required.
- **Always verify `Signed-off-by:` and `Assisted-by:` in both the final
  commit message and the exported patch.** `git gcc-verify` does not check
  either trailer.
- **Branches go off `upstream/master`**, not off other fix branches.
- **One fix per branch** (e.g., `pr123949-init-se-fix`), not stacked.

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

## Issue management (krystophny/gcc-dev)

Each GCC PR tracked in this repo has a GitHub issue. Issues use additive labels
to track progress through the submission pipeline:

| Label | Meaning |
|-------|---------|
| `patch-ready` | Working patch exists on the fork |
| `on-bugzilla` | Patch/analysis posted to GCC Bugzilla |
| `on-mailing-list` | Patch sent to gcc-patches@ mailing list |
| (closed) | Merged upstream |

Labels are additive: an issue can have all three simultaneously.

### When adding labels, always include a comment with links:

- **on-bugzilla**: link to the Bugzilla bug
  `https://gcc.gnu.org/bugzilla/show_bug.cgi?id=<number>`
- **on-mailing-list**: link to the mailing list archive post
  `https://gcc.gnu.org/pipermail/gcc-patches/YYYY-Month/NNNNNN.html`

### When closing issues (merged upstream), always include:

- Link to the upstream commit:
  `https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=<hash>`
- The GCC revision tag (e.g., `r16-7700-ge0b70284cfa`)

Example close comment:
```
Merged upstream: r16-7700-ge0b70284cfa
https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=e0b70284cfa...
```
