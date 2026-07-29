# Fix Issues

Automated end-to-end GCC Fortran issue fixing machine.

## Invocation

```
/fix-issues                     # Fix 1 top-priority unassigned Fortran regression
/fix-issues 3                   # Fix top 3
/fix-issues 79524 87352         # Fix specific PR numbers
```

## Priority Selection (when no PRs given)

Pick from open GitHub issues labeled `regression` + `bug`, excluding:
- Issues labeled `openacc` or `openmp` (out of scope for pure Fortran work)
- Issues already labeled `patch-ready`
- Issues with `needs-triage` label

Sort by: P1 > P2 > P3 > P4 > P5, then by lowest PR number (oldest first).

If a count N is given, pick top N. If nothing is given, pick 1.

Use:
```bash
gh issue list --repo lazy-fortran/gcc --state open --limit 500 --json number,title,labels \
  | python3 -c "
import json, re, sys
issues = json.load(sys.stdin)
result = []
for i in issues:
    labels = {l['name'] for l in i.get('labels', [])}
    if 'regression' not in labels or 'bug' not in labels:
        continue
    if labels & {'openacc', 'openmp', 'patch-ready', 'needs-triage'}:
        continue
    m = re.match(r'^[Pp][Rr](\d+)', i['title'])
    if not m:
        continue
    prio = 5
    for l in labels:
        if re.match(r'^P(\d)$', l):
            prio = int(l[1:])
    result.append({'number': i['number'], 'pr': int(m.group(1)), 'title': i['title'], 'prio': prio})
result.sort(key=lambda x: (x['prio'], x['pr']))
for r in result:
    print(f\"P{r['prio']} PR{r['pr']} #{r['number']} {r['title']}\")
"
```

## Workflow Per Issue

For EACH selected issue, execute this pipeline using agents in sequence.
Use TaskCreate to track progress. Create a plan first with EnterPlanMode.

### Phase 1: Reproduce and Understand

1. Read `pr/<number>/README.md` if it exists for prior analysis
2. Pull FULL Bugzilla context (mandatory, never the summary alone):
   ```bash
   scripts/gcc-bugzilla.sh info <number>
   scripts/gcc-bugzilla.sh comments <number>
   scripts/gcc-bugzilla.sh attachments <number>
   ```
   Distill root-cause hints, duplicates, and failed prior approaches into
   a few lines of `pr/<number>/README.md`; never paste Bugzilla verbatim.
3. Extract or write `pr/<number>/reproducer.f90` (provenance rules apply)
4. Verify it fails on current trunk:
   ```bash
   gcc-build/gcc/gfortran -B gcc-build/gcc reproducer.f90 -o /tmp/test-pr<number> 2>&1
   ```
5. Understand the root cause by reading relevant GCC Fortran source files

### Phase 2: Fix

1. Create a local branch in gcc/ off origin/main (lazy-fortran/gcc):
   ```bash
   git -C gcc fetch origin
   git -C gcc checkout -b fix/pr<number>-<slug> origin/main
   ```
2. Implement the minimal fix
3. Rebuild:
   ```bash
   cd gcc-build/gcc && make -j32
   ```
4. Verify the reproducer now works
5. Write a testcase in `gcc/testsuite/gfortran.dg/pr<number>.f90` with DejaGnu directives
6. Run the single test:
   ```bash
   cd gcc-build/gcc && make check-gfortran RUNTESTFLAGS="dg.exp=pr<number>.f90"
   ```

### Phase 3: Review (patrick-reviewer agent)

Spawn patrick-reviewer agent:
```
Review the fix for GCC Fortran PR<number> in the gcc/ repository.
Branch: pr<number>-fix (diff against upstream/master).
Check: correctness, minimal invasiveness, edge cases, GCC coding style.
The fix must not introduce regressions.
```

If patrick finds issues, revise the fix and re-review until clean.

### Phase 4: Full Test Suite

Run BOTH mandatory test suites. This is non-negotiable.

```bash
cd gcc-build/gcc && make -j32 -k check-gfortran > /tmp/check-gfortran-pr<number>.log 2>&1
cd gcc-build && make -j32 check-target-libgomp-fortran > /tmp/libgomp-fortran-pr<number>.log 2>&1
```

Check results:
```bash
grep -cE "^FAIL|^XPASS" gcc-build/gcc/testsuite/gfortran/gfortran.sum
```

If ANY new failures: fix them. Re-run. Repeat until zero new FAIL/XPASS.

### Phase 5: Commit and Open the PR

Follow GCC commit rules from CLAUDE.md exactly (Assisted-by in the body
above the PR line; Signed-off-by last):
```bash
cat > /tmp/gcc-commit-msg.txt <<'MSGEOF'
fortran: Short summary [PR<number>]

Description of the fix.

Fixes #<fork-issue-number>

Assisted-by: Claude (Anthropic)
MSGEOF
cd gcc && GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<number>"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt
git gcc-verify HEAD
git log -1 --format=%B | grep -q '^Signed-off-by: ' || echo "ERROR: missing Signed-off-by"
```

Push and open a REAL PR immediately (never a draft). PR title and body
ARE the verified commit message (the repo squash setting reproduces
them as the merge commit); the quick-read summary goes in the first PR
comment:
```bash
git -C gcc push origin fix/pr<number>-<slug>
gh pr create --repo lazy-fortran/gcc --base main \
  --head fix/pr<number>-<slug> \
  --title "$(git -C gcc log -1 --format=%s)" \
  --body "$(git -C gcc log -1 --format=%b)"
gh pr comment <pr-url> --repo lazy-fortran/gcc --body \
  "Fixes PR fortran/<number>: <one-line symptom>. Bugzilla: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=<number>. Tests: check-fortran + libgomp-fortran clean; new gfortran.dg/pr<number>.f90."
```

### Phase 6: Stop — the PR stays open

Do NOT merge. The PR stays open until reviewers are satisfied or the
user declares it OK. Patch attachments to Bugzilla are forbidden (GCC
AI policy). The only Bugzilla write is the PR-link comment via
`scripts/bugzilla-pr-notify.sh` (docs/patch-workflow.md step 7b):
hand-written, states what the patch changes, test evidence, relation
to prior patches on the bug. No AI disclaimer.

### Phase 7: Update Meta-Repo

1. Update `pr/<number>/README.md` with a short status note
2. Add the `patch-ready` label to the lazy-fortran/gcc issue and comment
   with the PR link (one line)
3. Commit and push meta-repo changes
4. Report the open PR(s) to the user for review/approval

## Important Rules

- Never skip the full test suite. Partial passes = failure.
- NEVER attach patches to Bugzilla. The only permitted Bugzilla write
  is the `bugzilla-pr-notify.sh` PR-link comment (body rules in
  docs/upstream-submission.md).
- All public text follows the desloppification rule in CLAUDE.md:
  plain sentences, concrete facts, no filler.
- One fix per branch (`fix/pr<number>-<slug>` off origin/main), never
  stacked, never drafts.
- Use gcc-commit-mklog for commit messages (never hand-write ChangeLog).
- Always run gcc-verify before pushing.
- Keep PR descriptions and issue comments short and targeted.
- If a bug is too complex or requires middle-end changes, report back to
  the user instead of attempting a fragile fix.
