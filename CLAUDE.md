# GCC Fortran Development Meta-Repository

## Repository Structure

This is a **meta-repository** that wraps the upstream GCC source tree and
organizes our development workflow. The meta-repo itself is tracked on GitHub;
the GCC source inside is a separate git repository.

```
gcc-dev/                    # META-REPO (tracked on GitHub, main branch)
│
├── gcc/                    # UPSTREAM GCC SOURCE (separate git repo)
│   │                       # Local branches only - NEVER push to upstream
│   └── gcc/
│       ├── fortran/        # Fortran frontend source code
│       └── testsuite/
│           └── gfortran.dg/  # Fortran DejaGnu test suite
│
├── gcc-build/              # OUT-OF-TREE BUILD (not tracked)
│   └── gcc/                # Run tests HERE: make check-gfortran
│
└── pr/                     # BUG WORK (tracked in meta-repo)
    ├── 92613/              # One directory per PR number
    │   ├── reproducer.f90  # Minimal test case
    │   ├── Makefile        # Multi-compiler testing
    │   ├── *.patch         # Exported patches
    │   └── README.md       # Analysis notes
    ├── 121472/
    └── ...
```

**Key concepts:**
- **Meta-repo** (`gcc-dev/`): Tracks our patches, reproducers, docs. Push to GitHub.
- **GCC source** (`gcc/`): Upstream code. Create local topic branches, export
  patches, but NEVER push to gcc.gnu.org (use `git send-email` instead).
- **Build dir** (`gcc-build/`): Out-of-tree build. Not version controlled.
- **PR dirs** (`pr/<number>/`): Each bug gets its own directory with reproducer,
  patches, and analysis.

**Git conventions:**
```bash
# Working with upstream GCC (from meta-repo root):
git -C gcc status
git -C gcc checkout -b pr12345-fix-something
git -C gcc format-patch -1 HEAD -o ../pr/12345/

# Working with meta-repo:
git add pr/12345/
git commit -m "pr12345: add reproducer and initial patch"
git push origin main
```

- `origin` = GitHub fork (safe to push for both repos)
- `upstream` = gcc.gnu.org (NEVER push, export patches instead)
- NEVER edit ChangeLog files; content comes from commit messages

## Build and Test

### Building
```bash
cd gcc-build && make -j$(nproc)
```

### Reconfiguring (Fortran-only, non-bootstrap)
```bash
rm -rf gcc-build && mkdir gcc-build && cd gcc-build
../gcc/configure --enable-languages=fortran --disable-multilib \
  --disable-bootstrap CFLAGS='-Og -g' CXXFLAGS='-Og -g'
```

### Running Tests

**CRITICAL: Run from `gcc-build/gcc/` only.**

```bash
cd /home/ert/code/gcc-dev/gcc-build/gcc
make -j$(nproc) -k check-gfortran > /tmp/test.log 2>&1 &
```

Wrong locations: meta-repo root, `gcc-build/`, `gcc/` source tree.

**Results:**
- Summary: `gcc-build/gcc/testsuite/gfortran/gfortran.sum`
- Log: `gcc-build/gcc/testsuite/gfortran/gfortran.log`

**Analyzing results:**
```bash
# Concise summary of failures:
./gcc/contrib/test_summary

# Quick check for unexpected failures:
grep -E "^FAIL|^XPASS" gcc-build/gcc/testsuite/gfortran/gfortran.sum
```

**Quick commands:**
```bash
# Single test:
make check-gfortran RUNTESTFLAGS="finalize_45.f90"

# Pattern:
make check-gfortran RUNTESTFLAGS="dg.exp=finalize*.f90"
```

**Verification:** Zero unexpected failures required for merge.

### Custom Compiler
```bash
gcc-build/gcc/gfortran -B gcc-build/gcc <file.f90>
```

## Reference Compilers

Always validate against multiple compilers:

| Compiler | Command |
|----------|---------|
| System gfortran | `/usr/bin/gfortran` |
| LLVM Flang | `/usr/bin/flang-new` |
| Intel ifx | `source /opt/intel/oneapi/setvars.sh && ifx` |
| NVIDIA nvfortran | `/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran` |
| LFortran | `lfortran` |

Intel ifx and NVIDIA nvfortran are best for F2018 compliance validation.

## Writing Test Cases

### Runtime Tests
Use `if/stop` pattern with unique exit codes:
```fortran
if (a%value /= 100) stop 1
if (.not. allocated(a%next)) stop 2
```

### DejaGnu Directives

**Do NOT use `dg-bogus` for warnings that should never appear.**
If code should compile cleanly, just use `dg-do compile`. Any unexpected
warning fails the test automatically.

Bad:
```fortran
! { dg-options "-Wall" }
! some code { dg-bogus "some warning" }
```

Good:
```fortran
! { dg-do compile }
! { dg-options "-Wall" }
! Code compiles cleanly - no dg-bogus needed
```

**Think through what the test verifies.** Consider all option combinations
(e.g., with/without `-E`). If an option combination is not useful, question
whether to support it at all.

## Coding Standards

### C vs C++

Prefer C for new code. Use C++ only when modifying existing C++ code where
C would be inconsistent. Keep data structures simple (linked lists, arrays).

### GNU Style and Formatting

**Line limits:**
- Lines ≤ 80 characters (hard limit)
- No trailing whitespace

**TAB and space rules (CRITICAL):**
- Indentation uses TABs, not spaces
- TAB width = 8 columns
- 8 consecutive spaces MUST be replaced with TAB
- Mixed indent: TAB(s) first, then spaces for fine alignment

**Spacing:**
- One space between function name and `(`
- Two spaces after `.` in comments (sentence separation)

**Automated checking:**
```bash
./gcc/contrib/check_GNU_style.sh gcc/fortran/<file>
```

**Manual verification (important for TAB/space issues):**
```bash
# Show TABs as ^I, line endings as $
cat -A <file> | head -50

# Find lines with 8+ consecutive spaces (should be TABs)
grep -n '        ' <file>

# Find trailing whitespace
grep -n ' $' <file>

# Find lines over 80 chars
awk 'length > 80 {print NR": "length" chars"}' <file>
```

**ChangeLog TAB verification:**
```bash
# TABs should show as ^I at start of ChangeLog lines
git log -1 --format=%B | cat -A
```

### Code Comments

**Keep comments minimal.** One or two lines maximum. Reference the PR number.
Do not explain what is obvious from the code or repeat the commit message.

Bad:
```c
  /* PR fortran/92613: For normal compilation of already preprocessed
     Fortran (-fpreprocessed without -E), skip libcpp tokenization
     entirely.  The C preprocessor does not understand Fortran comments
     (which start with !) and would incorrectly warn about apostrophes
     in comments like "! it's good".  Just load the already-preprocessed
     source directly in that case.  For -E (preprocess-only), keep using
     libcpp so that generic -fpreprocessed semantics still apply.  */
```

Good:
```c
  /* PR92613: Skip libcpp for -fpreprocessed without -E.  */
```

### Documentation

Avoid filler words. "preprocessed" not "fully preprocessed". Every word
must earn its place.

## Patch Development

### Workflow

1. Create topic branch: `git -C gcc checkout -b pr<number>-<short-desc>`
2. Develop iteratively, amending the single commit
3. Verify: `git -C gcc log -1 --format=%B | cat -A` (TABs show as `^I`)
4. Export: `git -C gcc format-patch -1 HEAD -o ../pr/<number>/`
5. Track: `git add pr/<number>/ && git commit -m "pr<number>: description"`

**Principles:**
- ONE commit per PR
- ChangeLog in commit message only (never in files)
- TAB formatting verified
- Signed-off-by present
- Tests passing

### Commit Message Format

```
fortran: Short summary (max 50 chars)

Detailed description explaining WHY.

	PR fortran/NNNNN

gcc/fortran/ChangeLog:

	* file.cc (function): Change description.

Signed-off-by: Name <email>
```

ChangeLog lines start with TAB. Verify with `cat -A`.

**Authorship:**
```bash
# For commits authored by others:
git commit --author="Name <email>" -m "message"

# For your own commits with sign-off:
git commit -s -m "message"
```

### Pre-Submission Checklist

**Style and formatting:**
- [ ] `./gcc/contrib/check_GNU_style.sh` passes on all modified/new files
- [ ] Lines ≤ 80 characters
- [ ] TABs not spaces (8-column stops)
- [ ] No trailing whitespace
- [ ] ChangeLog TAB formatting verified (`git log -1 --format=%B | cat -A`)

**Code quality:**
- [ ] Comments minimal (1-2 lines, PR number reference)
- [ ] No filler words in documentation
- [ ] Builds without warnings (`make -j$(nproc)`)
- [ ] All tests pass (`make -j$(nproc) -k check-gfortran`)
- [ ] No regressions in test suite
- [ ] New test case added for bug fix

**Design considerations:**
- [ ] All relevant option combinations mapped out
- [ ] Edge cases considered and tested
- [ ] Unusual option combinations: warn, error, or support silently?
- [ ] Test case verifies something meaningful (no useless `dg-bogus`)
- [ ] Reproducer tested with reference compilers (ifx, nvfortran)

## Fix Development Methodology

These rules prevent over-engineering and ensure minimal, correct fixes.

### 1. Start with the failing condition

Before writing any code, identify the EXACT condition that fails and what it
should be. Write it down:

```
CURRENT:  if (!derived->components)     -- catches empty types
FAILING:  type with empty components    -- has components, but zero size
CORRECT:  if (TYPE_SIZE_UNIT == 0)      -- catches ALL zero-size types
```

If you cannot write this down clearly, you do not understand the bug yet.

### 2. Minimal fix first, infrastructure later

**WRONG order:** Design infrastructure → implement → hope it fixes the bug
**RIGHT order:** Find minimal condition fix → verify it works → consider if
infrastructure is even needed

Most bugs are single-condition fixes. Multi-file infrastructure patches are
rarely necessary and often indicate the bug is not yet understood.

| Symptom | Likely reality |
|---------|----------------|
| Fix touches 3+ files | Probably over-engineered |
| Fix adds new parameters | Probably should refine existing condition |
| Fix adds new struct fields | Probably checking at wrong level |
| Fix requires "threading" changes through call sites | Probably wrong approach |

### 3. Check at the right level

| Level | Examples | Use when |
|-------|----------|----------|
| Fortran symbol | `derived->components`, `attr.allocatable` | Source-level semantics |
| Fortran f2k | `f2k_derived->tb_op[...]` | Type-bound procedures |
| Tree | `TYPE_SIZE_UNIT`, `TREE_TYPE` | Compiled representation |
| Gimple | gimplifier behavior | Low-level codegen issues |

**Rule:** If the bug manifests at level N, the fix usually needs level N info.

Gimplifier ICE? Check tree-level properties, not Fortran symbols.
Type-bound procedure issue? Check f2k_derived, not just symbol attributes.

### 4. Understand existing checks before adding new ones

Read the existing code and comments. Ask:
- What case was this check trying to handle?
- Why doesn't it catch my case?
- Can I extend it rather than add a parallel check?

**WRONG:**
```c
// Existing check
if (!derived->components) handle_zero_size();
// My new check (parallel, redundant)
if (TYPE_SIZE_UNIT == 0) handle_zero_size();
```

**RIGHT:**
```c
// Replace with more general check
if (TYPE_SIZE_UNIT == 0) handle_zero_size();
```

### 5. Refine conditions, don't add bypass parameters

When a condition is too broad, make it more precise. Don't add parameters
to bypass it.

**WRONG:**
```c
// Added parameter to bypass check
void func(..., bool bypass_check) {
  if (!bypass_check && some_condition)
    return;
}
```

**RIGHT:**
```c
// Refined the condition itself
void func(...) {
  if (more_precise_condition)
    return;
}
```

Parameters create API surface, require call-site changes, and hide the
real problem. Refined conditions fix the logic where it belongs.

### 6. Preserve existing comments when logic is unchanged

If you're changing HOW something is detected but not WHAT is done about it,
keep the original comment. It explains the reasoning that still applies.

```c
// KEEP this comment - still explains WHY we create a dummy var
/* Any attempt to assign zero length entities, causes the gimplifier
   all manner of problems. Instead, a variable is created to act as
   as the argument for the final call.  */
desc = gfc_create_var (type, "zero");
```

Only the detection changed (components → size), not the handling.

### 7. One logical change per patch

A patch should do ONE thing:
- Fix the ICE, OR
- Improve finalization semantics, OR
- Add infrastructure for future work

NOT all three. If you find yourself writing a patch that "fixes X and also
improves Y and adds infrastructure for Z", split it up or reconsider whether
Y and Z are actually needed.

### 8. Verify the fix matches the bug

After implementing, verify:
1. The original reproducer now works
2. The fix triggers for exactly the right cases (add debug print if needed)
3. No unrelated tests regress

If the fix is correct but seems to require touching many files, you likely
misidentified the root cause.

## Fortran Standards Compliance

All implementations must match ISO/IEC 1539-1:2018 exactly. No partial
compliance. Reference compilers (ifx, nvfortran) define correct behavior.

Key areas:
- Allocatable assignment: deallocate, reallocate, deep copy (7.5.2.3)
- Finalization: function results finalized after assignment (7.5.6.3)
- Self-assignment: special handling to avoid use-after-free

## PR Directory Organization

Each `pr/<number>/` contains:
- Reproducer programs (`.f90`)
- Patches (`.patch`)
- Makefile for multi-compiler testing

## Upstream Submission

**NEVER submit without explicit user permission.**

**Permitted (no approval needed):**
- Prepare patch files with `git format-patch`
- Generate commit messages with proper ChangeLog format
- Run local tests and validation
- Export patches to `pr/<number>/` directory
- Document submission readiness

**Requires explicit user permission:**
- Posting to mailing lists (fortran@gcc.gnu.org, gcc-patches@gcc.gnu.org)
- Updating Bugzilla
- Any external communication about patches
- Sending emails on behalf of the user

User controls timing and content of all upstream submissions.
