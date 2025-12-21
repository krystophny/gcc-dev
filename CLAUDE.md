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
```

**Key concepts:**
- **Meta-repo** (`gcc-dev/`): Tracks our patches, reproducers, docs. Push to GitHub.
- **GCC source** (`gcc/`): Upstream code. Create local topic branches, export
  patches, but NEVER push to gcc.gnu.org (use `git send-email` instead).
- **Build dir** (`gcc-build/`): Out-of-tree build. Not version controlled.
- **PR dirs** (`pr/<number>/`): Each bug gets its own directory with reproducer,
  patches, and analysis. Each `pr/<number>/` typically contains a reproducer,
  exported patch files, and (optionally) a Makefile for multi-compiler testing.

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

## Scope and Expertise

This repository focuses on a small, well-exercised subset of gfortran. Treat
work outside this scope as an explicit learning task (more archaeology, more
review), not as a quick patch.

### Strongest Areas (patches + regressions exist)

- Finalization lowering and ICEs: `trans.cc:gfc_finalize_tree_expr`,
  assignment/finalization interactions in `trans-expr.cc` and `interface.cc`.
  Evidence: PR90519, PR121472, PR121475.
- Recursive allocatable components: deep copy, recursion, and self-assignment
  hazards in `trans-array.cc` and related helpers. Evidence: PR90519, PR121628.
- Array constructors with explicit type-spec and folding: type conversion and
  character length propagation across parentheses, nesting, and CONCAT in
  `array.cc`, `arith.cc`, and `resolve.cc`. Evidence: PR107721.
- Preprocessing modes: interactions between `-cpp`, `-E`, and `-fpreprocessed`
  in `cpp.cc`, `scanner.cc`, and `f95-lang.cc`. Evidence: PR92613.
- Parsing/diagnostics and constrained semantics: targeted `match.cc`,
  `resolve.cc`, and `parse.cc` fixes with focused regressions. Evidence:
  PR32365, PR96255.

### Familiar but Not Yet Deep

- Polymorphism/CLASS lowering beyond the paths exercised by the PRs above.
- Interface/overload resolution beyond defined assignment interactions.
- Runtime/library behavior (`libgfortran`) except when needed to validate
  frontend semantics.

### Out of Scope by Default

- GCC middle-end/back-end work (GIMPLE/RTL optimizations, codegen), except when
  the frontend must satisfy a concrete tree-level contract.
- Broad refactors or new infrastructure without a minimal reproducer and a
  regression test.

### Extending Scope Safely

- Start with a minimal reproducer in `pr/<number>/reproducer.f90`.
- Identify the failing contract at the right level (symbol/f2k/tree/gimple)
  and apply the smallest condition fix that matches it.
- Add a DejaGnu regression that fails before and passes after.

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
cd gcc-build/gcc
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

## OpenACC NVPTX (GCC16 in /opt)

This meta-repo also supports building a local GCC with NVPTX offload
(OpenACC/OpenMP) into `/opt/gcc16`.

### Build and install

```bash
./scripts/build_gcc16_nvptx.sh --clean
```

This script:
- clones `third_party/newlib-cygwin` and `third_party/nvptx-tools`
- builds/installs nvptx-tools to `/opt/gcc16/nvptx`
- builds/installs the NVPTX accelerator (including `libgfortran.a`)
- builds/installs the host compiler with `--enable-offload-targets=nvptx-none`
- runs small OpenACC + OpenMP target offload smoke tests (logs under `/tmp`)

Note: OpenMP target offload requires the NVPTX `mgomp` multilib (for `__nvptx_uni`);
do not configure the NVPTX accelerator with `--disable-multilib`.

### Smoke test only

```bash
./scripts/openacc_nvptx_smoke.sh
./scripts/openmp_nvptx_smoke.sh
```

## Reference Compilers

Always validate against multiple compilers:

| Compiler | Command |
|----------|---------|
| System gfortran | `gfortran` |
| LLVM Flang | `flang-new` |
| Intel ifx | `source /opt/intel/oneapi/setvars.sh && ifx` |
| NVIDIA nvfortran | `nvfortran` (often under `/opt/nvidia/` on Linux) |
| LFortran | `lfortran` |

Intel ifx and NVIDIA nvfortran are best for standards compliance validation.

Note: on many Linux systems, vendor compilers are installed under `/opt/`
(commonly `/opt/intel/` and `/opt/nvidia/`). Prefer using the compiler on
`PATH`, but look under `/opt/` when setting up your environment.

## Writing Test Cases

### Runtime Tests
Use `if/stop` pattern with unique exit codes:
```fortran
if (a%value /= 100) stop 1
if (.not. allocated(a%next)) stop 2
```

### DejaGnu Directives

If a test must compile without warnings under specific options (e.g. `-Wall`),
make warnings actionable:
- Prefer `-Werror` when it is appropriate for the test.
- Use `dg-bogus` only when you must keep warnings non-fatal but still want to
  assert that a specific diagnostic does not appear.

Patterns:
```fortran
! { dg-do compile }
! { dg-options "-Wall -Werror" }
! Code must compile without warnings
```

```fortran
! { dg-do compile }
! { dg-options "-Wall" }
! { dg-bogus "Unused variable '_i' declared" }
! Use dg-bogus when you need to assert absence without -Werror
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

**Keep comments minimal.** One or two lines maximum. Do not explain what is
obvious from the code or repeat the commit message. Keep PR numbers out of
inline source code comments; put PR numbers in commit messages and tests.

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
  /* Skip libcpp for -fpreprocessed without -E.  */
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
| Fortran f2k | `f2k_derived->tb_op` | Type-bound procedures |
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
void func (tree expr, bool bypass_check) {
  if (!bypass_check && some_condition)
    return;
}
```

**RIGHT:**
```c
// Refined the condition itself
void func (tree expr) {
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

**Standard text files:** set `STANDARD_DIR` to your local checkout of the
standard text files (one-time per shell).

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
export STANDARD_DIR="$HOME/code/standard/validation/pdfs"
grep -n "7.5.6.3" "$STANDARD_DIR/Fortran2023_J3_22-007.txt"
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

### Key Files

- `trans.cc`: tree expression translation; finalization lowering.
- `trans-expr.cc`: expression translation; assignments and procedure calls.
- `trans-array.cc`: array operations; deep copy and allocatable components.
- `arith.cc`: constant folding; intrinsic evaluation.
- `array.cc`: array constructors; type-spec propagation and conversion.
- `resolve.cc`: semantic resolution; constraint enforcement.
- `match.cc`: syntax matching; statement recognition.
- `parse.cc`: statement parsing; ordering diagnostics.
- `interface.cc`: procedure interfaces; defined assignment and operators.
- `class.cc`: CLASS/polymorphic handling; vtables and wrappers.
- `scanner.cc`: source file reading; preprocessing integration.
- `cpp.cc`: C preprocessor interface; preprocessing modes.
- `gfortran.h`: frontend data structures.

### Where To Look First

| Symptom | First files to inspect | Key entry points / checks | Notes |
|---------|------------------------|---------------------------|-------|
| ICE in gimplifier | `trans.cc`, `trans-expr.cc`, `trans-array.cc` | Tree generation assumptions; shape/size properties | If gimplifier fails, the frontend built an invalid tree. |
| Missing/double finalization | `trans.cc`, `trans-expr.cc`, `class.cc`, `interface.cc` | `gfc_finalize_tree_expr` early returns; defined assignment interactions | Use tree-level checks for tree-level problems. |
| Deep copy / allocatable comps | `trans-array.cc`, `trans-expr.cc` | `structure_alloc_comps`, `duplicate_allocatable`, `gfc_copy_alloc_comp` | Self-assignment needs overlap protection. |
| Folding / array constructors | `arith.cc`, `array.cc`, `resolve.cc` | `eval_intrinsic`, `check_constructor_type`, `gfc_check_constructor_type`, `gfc_resolve_character_array_constructor` | Simplify wrapper nodes (e.g. parentheses) before conversion; preserve character length metadata. |
| Parse / new syntax | `match.cc`, `resolve.cc`, `gfortran.h` | `gfc_match_*` paths; new fields and semantic checks | New syntax usually touches parsing + data + resolution. |
| Diagnostics | `parse.cc`, `resolve.cc`, `error.cc` | Statement ordering and constraint checks | Prefer targeted cases over new infrastructure. |
| Preprocessing | `cpp.cc`, `scanner.cc`, `f95-lang.cc` | `gfc_cpp_enabled`, `gfc_option.flag_preprocessed`, `gfc_cpp_preprocess_only` | Option combinations matter (`-E`, `-cpp`, `-fpreprocessed`). |

### Typical Change Points (by domain)

These are the places we most often change code successfully, based on the PRs
tracked in `pr/`.

#### Finalization and derived-type lowering

- Change points:
  - Refine early-return conditions in `gfc_finalize_tree_expr` (skip only when
    semantics require skipping).
  - Use tree-level properties when the failure is tree-level (e.g. size/shape
    checks) rather than Fortran-symbol heuristics.
  - Keep handling logic stable when only detection changes.
- Avoid:
  - Adding bypass parameters to thread through call sites.
  - Adding broad new metadata tracking when the failing condition is a single
    missing check.

#### Recursive allocatable components and deep copy

- Change points:
  - Ensure deep copy recurses through nested allocatable components in
    `structure_alloc_comps`.
  - Handle self-assignment/overlap before deallocation or deep copy.
  - Prefer non-trampoline helper generation over nested functions.
- Avoid:
  - Creating executable-stack requirements (nested wrappers/trampolines).
  - Relying on superficial pointer comparisons without stripping syntactic
    wrappers.

#### Array constructors, type-spec, and folding

- Change points:
  - Simplify wrapper nodes (parentheses, expression operators) before
    conversion/type checking in constructor validation paths.
  - Ensure type-spec conversion runs before folding/operations like CONCAT.
  - Preserve character length information when building result expressions.
  - For nested constructors with their own type-spec, resolve inner semantics
    first, then propagate outer semantics and resolve again.
- Avoid:
  - Converting the wrapper node while leaving the wrapped expression untouched.
  - Doing folding that drops type-spec-derived length information.

#### Preprocessing modes (`-cpp`, `-E`, `-fpreprocessed`)

- Change points:
  - Make option combinations explicit (preprocess-only vs normal compilation).
  - Skip libcpp when the input is already preprocessed and the driver is not
    in preprocess-only mode.
- Avoid:
  - Treating `-fpreprocessed` as a request to run the preprocessor anyway.
  - Adding warning-suppression tests; prefer fixing the behavior so warnings do
    not occur.

#### Parsing, resolution, and diagnostics

- Change points:
  - Implement syntax in `match.cc` with tight backtracking.
  - Enforce constraints and typing in `resolve.cc` with a regression that
    exercises the semantic rule.
  - Improve diagnostics in `parse.cc` with a targeted case; keep it narrow.
- Avoid:
  - New global state or new infrastructure when a single case in an existing
    switch can enforce the rule.
  - Vague tests that only check that something compiles.

### What Not To Do (hard-won defaults)

- Do not add new infrastructure until the failing condition is written down
  precisely and a minimal reproducer exists.
- Do not add bypass parameters; refine the condition where the logic belongs.
- Do not duplicate checks; replace the old one with a strictly more general
  check when appropriate.
- Do not rely on line numbers or local paths in documentation and commands.
- Do not use `dg-bogus` to paper over warnings that should not exist; prefer
  making warnings actionable (often with `-Werror`) when that matches the test.

Examples (for quick recall):
- PR107721: fixed folding for array constructors with explicit type-spec (parentheses, nesting, CONCAT); resolved nested type-specs before propagation.
- PR121472: zero-size derived type ICE fixed by checking size properties, not component presence.
- PR121475: refined overly broad finalization early-return condition for defined assignment.
- PR121628: avoided nested function trampolines by generating top-level helpers.
- PR96255: DO CONCURRENT type-spec required coordinated `match.cc` + `resolve.cc` + `gfortran.h` updates.
- PR32365: improved statement-ordering diagnostic in `parse.cc`.
- PR92613: preprocessing mode interaction fixed by skipping libcpp for already-preprocessed input.

Anti-pattern reminders (see Fix Development Methodology above):
- Prefer minimal condition fixes over new infrastructure.
- Refine conditions instead of adding bypass parameters.
- Match the check level to where the bug manifests.
- Replace subsumed checks; do not add parallel checks.

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

Checklist:
- Save `gfc_current_locus` for backtracking.
- Match tokens in small steps; on failure restore the locus and return `MATCH_NO`.
- Only build AST nodes after a successful syntactic match.
- Keep one logical syntax change per patch; add semantic enforcement in `resolve.cc` when needed.

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
