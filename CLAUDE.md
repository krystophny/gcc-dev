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

### 9. Keep PR numbers out of inline code comments

PR numbers belong in:
- Commit messages (required)
- Test file comments (e.g., `! PR fortran/121472`)
- README documentation

PR numbers do NOT belong in:
- Inline source code comments

The code comment should explain WHAT/WHY in timeless terms. The PR number
is metadata tracked elsewhere.

**WRONG:**
```c
/* PR121472: Zero-length entities cause gimplifier problems.  */
```

**RIGHT:**
```c
/* Zero-length entities cause the gimplifier problems.  Create
   a variable to act as the argument for the final call.  */
```

## Fortran Standards Compliance

**Current standard:** ISO/IEC 1539-1:2023 (Fortran 2023)

**Standard text files:** `/home/ert/code/standard/validation/pdfs/`

| Standard | Text file |
|----------|-----------|
| Fortran 2023 | `Fortran2023_J3_22-007.txt` |
| Fortran 2018 | `Fortran2018_J3_15-007.txt` |
| Fortran 2008 | `Fortran2008_J3_08-007.txt` |
| Fortran 2003 | `Fortran2003_J3_03-007.txt` |
| Fortran 95 | `Fortran95_WG5_N1191.txt` |
| Fortran 90 | `Fortran90_WG5_N692.txt` |

Use `grep` to search for specific clauses:
```bash
grep -n "7.5.6.3" /home/ert/code/standard/validation/pdfs/Fortran2023_J3_22-007.txt
```

All implementations must match ISO/IEC 1539-1:2023 exactly. No partial
compliance. Reference compilers (ifx, nvfortran) define correct behavior.

**Key sections for derived type semantics:**

| Section | Topic |
|---------|-------|
| 7.5.4 | Components |
| 7.5.5 | Type-bound procedures |
| 7.5.6 | Final subroutines |
| 7.5.6.2 | The finalization process |
| 7.5.6.3 | When finalization occurs |
| 7.5.6.4 | Entities that are not finalized |
| 10.2.1.2 | Intrinsic assignment statement |
| 10.2.1.3 | Interpretation of intrinsic assignments |
| 10.2.1.4 | Defined assignment statement |

**Finalization rules (7.5.6.3):**
- Function results finalized after execution of innermost executable construct
- Intent(out) arguments finalized on entry
- Allocated allocatables finalized on deallocation
- Pointers are NOT finalized (only targets when deallocated)

**Self-assignment:** Requires special handling to avoid use-after-free when
source and target overlap.

## GCC Fortran Codebase Analysis

This section documents patterns learned from working on PRs 32365, 90519,
92613, 96255, 107721, 121472, 121475, and 121628.

### Source File Map

| File | Responsibility | Common fixes |
|------|----------------|--------------|
| `trans.cc` | Tree expression translation, finalization | Finalization conditions, zero-size handling |
| `trans-expr.cc` | Expression translation, assignments | Assignment semantics, procedure calls |
| `trans-array.cc` | Array operations, deep copy | Allocatable component handling, temp arrays |
| `resolve.cc` | Semantic resolution | Type checking, constraint enforcement |
| `match.cc` | Parsing, syntax matching | New syntax features, statement recognition |
| `parse.cc` | Statement parsing, ordering | Statement sequence validation |
| `interface.cc` | Procedure interfaces | Defined assignment, operator resolution |
| `class.cc` | CLASS/polymorphic handling | Vtable, finalization wrappers |
| `scanner.cc` | Source file reading | Preprocessing, include handling |
| `cpp.cc` | C preprocessor interface | Preprocessing modes |
| `gfortran.h` | Data structures | New flags, struct fields |

### Bug Categories and Where to Fix

#### 1. ICE in Gimplifier

**Symptoms:** `internal compiler error: in gimplify_expr` or similar

**Cause:** Invalid tree generated by Fortran frontend

**Where to look:**
- `trans.cc` - Check conditions before generating trees
- `trans-expr.cc` - Check expression translation
- `trans-array.cc` - Check array/allocatable handling

**Example (PR121472):** Zero-size derived type caused gimplifier failure.
Fix was in `trans.cc:gfc_finalize_tree_expr` - check `TYPE_SIZE_UNIT`
instead of `derived->components`.

**Pattern:** If gimplifier fails, the bug is in tree generation, not
gimplifier. Check what tree properties the frontend assumes vs. provides.

#### 2. Finalization Issues

**Symptoms:** Missing destructor calls, double finalization, memory leaks

**Key function:** `gfc_finalize_tree_expr` in `trans.cc`

**Early return conditions (lines ~1620-1630):**
```c
if (attr.pointer) return;
if (derived->attr.is_c_interop || ... || derived->attr.defined_assign_comp)
  return;
```

**Common mistakes:**
- Early return too broad (PR121475: `defined_assign_comp` blocked valid cases)
- Early return too narrow (PR121472: `!derived->components` missed some cases)

**Fix pattern:** Refine conditions to match exactly when finalization should
be skipped. Use tree-level checks for tree-level issues.

#### 3. Deep Copy / Allocatable Components

**Key files:**
- `trans-array.cc:structure_alloc_comps` - Recursive component traversal
- `trans-array.cc:duplicate_allocatable` - Allocation + memcpy
- `trans-array.cc:gfc_copy_alloc_comp` - Public API

**Trampoline issue (PR121628):** Nested function wrappers required executable
stack. Fix: Use top-level function generation instead of `push_function_context`.

**Self-assignment:** Must check `lhs == rhs` at runtime before deep copy to
avoid use-after-free. Strip `INTRINSIC_PARENTHESES` before comparing.

#### 4. Parsing / New Syntax Features

**Key file:** `match.cc`

**Example (PR96255):** DO CONCURRENT type-spec required:
1. Match optional `integer ::` prefix in `match_forall_header`
2. Create shadow variables when type differs from outer scope
3. Update `gfortran.h` with new struct fields

**Pattern:** New syntax = `match.cc` changes + `gfortran.h` data structures
+ `resolve.cc` semantic checks.

#### 5. Diagnostics / Error Messages

**Key file:** `parse.cc` for statement ordering errors

**Example (PR32365):** Improved "specification statement in executable
section" message. Fix was in `parse_executable` - catch specification
statements after executable statements and give clear error.

**Pattern:** Better diagnostics rarely need new infrastructure. Usually
it's adding a specific case to an existing switch statement.

#### 6. Preprocessing Issues

**Key files:** `cpp.cc`, `scanner.cc`, `f95-lang.cc`

**Example (PR92613):** `-fpreprocessed` with `-cpp` caused bogus warnings.
Fix: Skip libcpp entirely for `-fpreprocessed` mode.

**Coordination points:**
- `gfc_cpp_enabled()` - Is preprocessor active?
- `gfc_option.flag_preprocessed` - Is input already preprocessed?
- `gfc_cpp_preprocess_only()` - Is this `-E` mode?

### Anti-Patterns We Learned to Avoid

#### 1. Adding Infrastructure Before Understanding the Bug

**PR121472 complex fix:** 6 files, 212 lines, temp metadata tracking
**PR121472 simple fix:** 1 file, 3 lines, condition change

The complex fix assumed the problem was temp tracking. The actual bug was
a single condition checking component existence instead of type size.

**Rule:** Find the minimal condition fix first.

#### 2. Adding Parameters to Bypass Checks

**PR121475 complex fix:** Added `finalize_func_result` parameter to bypass
`defined_assign_comp` check.

**PR121475 simple fix:** Refined the condition itself to be more precise
about when defined assignment actually applies.

**Rule:** Refine conditions, don't add bypass parameters.

#### 3. Checking at Wrong Abstraction Level

| Bug level | Wrong check | Right check |
|-----------|-------------|-------------|
| Gimplifier | `derived->components` | `TYPE_SIZE_UNIT` |
| Type-bound procedure | `attr.defined_assign_comp` | `f2k_derived->tb_op` |
| Source syntax | Tree properties | Symbol attributes |

**Rule:** Match check level to bug manifestation level.

#### 4. Parallel Checks Instead of Unified Check

**Wrong:**
```c
if (new_condition) handle();
else if (old_condition) handle();  // Redundant
```

**Right:**
```c
if (general_condition_that_covers_both) handle();
```

If your new check subsumes an existing check, replace don't add.

#### 5. Over-Commenting with PR Numbers

PR numbers in code clutter the source. The commit message and test file
have the PR number. Code comments should explain the logic timelessly.

### Code Structure Patterns

#### gfc_finalize_tree_expr Flow

```
1. Early returns (pointer, C interop, defined_assign_comp)
2. CLASS handling (polymorphic)
3. Derived type handling (gfc_is_finalizable)
   a. Zero-size check → create dummy var
   b. direct_byref path
   c. Normal path → evaluate, maybe copy alloc_comp
4. Build finalization call via vtable
```

Most finalization bugs are in step 1 (wrong early return) or step 3a
(incomplete zero-size detection).

#### structure_alloc_comps Flow (Deep Copy)

```
1. Iterate over derived type components
2. For each allocatable component:
   a. Check allocation status
   b. Allocate destination
   c. memcpy data
   d. Recurse for nested allocatable components
3. Handle CLASS components specially via vptr
```

Deep copy bugs usually involve missing recursion or wrong allocation status
checks.

#### match_* Functions Pattern

```c
gfc_match_result
gfc_match_xxx (void)
{
  // Save position for backtrack
  old_loc = gfc_current_locus;

  // Try to match syntax
  m = gfc_match ("keyword");
  if (m != MATCH_YES) {
    gfc_current_locus = old_loc;
    return MATCH_NO;
  }

  // Build AST structures
  // ...

  return MATCH_YES;
}
```

### Quick Reference: Common Fixes by Symptom

| Symptom | First place to look |
|---------|---------------------|
| ICE in gimplify | `trans*.cc` - tree generation |
| Missing finalization | `trans.cc:gfc_finalize_tree_expr` early returns |
| Double finalization | Same, plus `trans-expr.cc` assignment handling |
| Wrong deep copy | `trans-array.cc:structure_alloc_comps` |
| Parse error | `match.cc` or `parse.cc` |
| Bad diagnostic | `parse.cc`, `resolve.cc`, or `error.cc` |
| Preprocessing | `cpp.cc`, `scanner.cc` |

### Files Changed Per PR (Reference)

| PR | Files | Topic |
|----|-------|-------|
| 32365 | parse.cc | Error messages |
| 90519 | class.cc, trans-expr.cc | Finalizer + recursive alloc |
| 92613 | cpp.cc, scanner.cc, f95-lang.cc | Preprocessing |
| 96255 | match.cc, resolve.cc, gfortran.h | DO CONCURRENT syntax |
| 107721 | resolve.cc (character arrays) | Array constructor |
| 121472 | trans.cc | Finalization + zero-size |
| 121475 | trans.cc, interface.cc | Defined assignment + finalization |
| 121628 | trans-array.cc | Deep copy trampolines |

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
