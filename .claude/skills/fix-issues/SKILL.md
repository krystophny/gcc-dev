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
2. Get the reproducer from Bugzilla:
   ```bash
   scripts/gcc-bugzilla.sh comments <number>
   ```
3. Extract or write `pr/<number>/reproducer.f90`
4. Verify it fails on current trunk:
   ```bash
   gcc-build/gcc/gfortran -B gcc-build/gcc reproducer.f90 -o /tmp/test-pr<number> 2>&1
   ```
5. Understand the root cause by reading relevant GCC Fortran source files

### Phase 2: Fix

1. Create a local branch in gcc/ off upstream/master:
   ```bash
   git -C gcc fetch upstream master
   git -C gcc checkout -b pr<number>-fix upstream/master
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

### Phase 5: Commit and Export Patch

Follow GCC commit rules from CLAUDE.md exactly:
```bash
cat > /tmp/gcc-commit-msg.txt <<'MSGEOF'
fortran: Short summary [PR<number>]

Description of the fix.
MSGEOF
cd gcc && GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<number>"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt
git gcc-verify HEAD
git log -1 --format=%B | grep -q '^Signed-off-by: ' || echo "ERROR: missing Signed-off-by"
git format-patch -1 HEAD -o ../pr/<number>/
git checkout master
git branch -D pr<number>-fix
```

Patch work is stored as exported `.patch` files under `pr/<number>/`; no
persistent `pr*-fix` branches on the fork.

### Phase 6: Post to Bugzilla

Post the patch and a comment describing the fix:
```bash
scripts/gcc-bugzilla.sh attach <number> pr/<number>/0001-*.patch "Patch: <summary>"
scripts/gcc-bugzilla.sh comment <number> "Patch posted. <brief description of the fix and test results.>"
```

### Phase 7: Update Meta-Repo

1. Update `pr/<number>/README.md` with status
2. Add `patch-ready` and `on-bugzilla` labels to the GitHub issue
3. Commit and push meta-repo changes

## Important Rules

- Never skip the full test suite. Partial passes = failure.
- Bugzilla posts (patches, comments) are pre-approved and do not need user confirmation.
- One fix per branch, branching off upstream/master.
- Use gcc-commit-mklog for commit messages (never hand-write ChangeLog).
- Always run gcc-verify before pushing.
- If a bug is too complex or requires middle-end changes, report back to the user instead of attempting a fragile fix.
