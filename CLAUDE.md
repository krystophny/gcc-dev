# GCC Fortran Development Meta-Repository

## Repository Layout

This meta-repository tracks GCC Fortran bug reproducers, patches, and development workflows.

**Directory Structure:**
- `/home/ert/code/gcc-dev/` - Meta-repo root (tracked on `main` branch, pushable to GitHub)
- `/home/ert/code/gcc-dev/gcc/` - Upstream GCC repository (local branches only, never push)
- `/home/ert/code/gcc-dev/gcc-build/` - Build artifacts
- `/home/ert/code/gcc-dev/pr/` - Bug reproducers and patches, organized by PR number

**Git Command Conventions:**
- Upstream GCC work: `git -C gcc <command>` (from meta-repo root)
- Meta-repo work: `git <command>` (from meta-repo root)
- **Push targets matter:**
  - `origin` (GitHub private fork) is safe for both repos—push topic branches here whenever we need to share WIP.
  - `upstream` (gcc.gnu.org) must NEVER receive pushes; export patches or use `git send-email` instead.
- **Do not edit GCC ChangeLog files** - upstream regenerates them from commit metadata. NEVER touch the ChangeLog entries by hand; all ChangeLog content must come from the git commit message when patches are exported upstream.

## Build and Test Workflow

### Building GCC
```bash
cd gcc-build
make -j32
```

#### Reconfiguring for a non-bootstrap Fortran-only build
If the build directory was configured differently (for instance by a prior
bootstrap), wipe and recreate it before rebuilding:
```bash
rm -rf gcc-build
mkdir gcc-build
cd gcc-build
../gcc/configure --enable-languages=fortran --disable-multilib \
  --disable-bootstrap CFLAGS='-Og -g' CXXFLAGS='-Og -g'
```
This mirrors the `bootstrap.sh` helper script and produces a single-stage,
debuggable Fortran toolchain (no bootstrap/checking, optimized with `-Og`).

### Running Test Suite
**CRITICAL: Test suite MUST be run from `gcc-build/gcc/` directory**

**Correct workflow:**
```bash
# From meta-repo root:
cd /home/ert/code/gcc-dev/gcc-build/gcc

# Run test suite in background:
make -j32 check-gfortran > /tmp/test-output.log 2>&1 &

# Alternative: use -k flag to continue on errors:
make -j32 -k check-gfortran > /tmp/test-output.log 2>&1 &
```

**WRONG - Do NOT run from these locations:**
- ❌ `/home/ert/code/gcc-dev/` (meta-repo root - no target)
- ❌ `/home/ert/code/gcc-dev/gcc-build/` (build root - no target)
- ❌ `/home/ert/code/gcc-dev/gcc/` (source tree - no target)
- ✅ `/home/ert/code/gcc-dev/gcc-build/gcc/` (CORRECT location)

**Test results location:**
- Summary: `gcc-build/gcc/testsuite/gfortran/gfortran.sum`
- Detailed log: `gcc-build/gcc/testsuite/gfortran/gfortran.log`
- Look for: `# of expected passes`, `# of unexpected failures`

**Verification checklist:**
- Zero unexpected failures required for merge
- All new tests passing
- No regressions in existing tests

### Custom Compiler Invocation
```bash
gcc-build/gcc/gfortran -B gcc-build/gcc <file.f90>
```

### Reference Compilers for Behavior Validation

**ALWAYS test bug reproducers and fixes against multiple compilers to validate behavior:**

**Available Compilers:**

1. **System gfortran (GCC 15.2.1)**
   ```bash
   /usr/bin/gfortran <file.f90>
   ```
   - Primary reference for correct F2018+ behavior
   - Validated for finalization semantics

2. **LLVM Flang (flang-new 21.1.5)**
   ```bash
   /usr/bin/flang-new <file.f90>
   ```
   - LLVM-based Fortran compiler
   - Use for cross-compiler validation

3. **Intel ifx (IFX 2025.2.1)**
   ```bash
   # Source environment first:
   source /opt/intel/oneapi/setvars.sh

   # Then compile:
   /opt/intel/oneapi/compiler/2025.2/bin/ifx <file.f90>
   ```
   - Intel oneAPI Fortran compiler
   - Use for Intel-specific behavior and optimization validation

4. **NVIDIA nvfortran (25.9-0)**
   ```bash
   /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran <file.f90>
   ```
   - NVIDIA HPC SDK Fortran compiler
   - Use for HPC/GPU Fortran validation
   - Excellent for standards compliance testing

5. **LFortran**
   ```bash
   lfortran <file.f90>
   ```
   - Interactive Fortran compiler
   - Modern, fast compiler with good diagnostics
   - Use for additional F2018+ feature validation
   - Note: Some F2018 features may not be fully implemented yet

**Testing Protocol:**
- Always test reproducers with at least 2-3 compilers
- Document which compilers show the bug
- Document which compilers show correct behavior
- Compare output for semantic correctness

### Test Suite Conventions

**Runtime Test Patterns:**
- **PREFERRED**: Use `if (result /= expected) stop n` pattern for runtime tests
- Provides clear pass/fail with specific error codes
- Easier to read and maintain than pattern matching
- Each test condition should have unique stop number (1, 2, 3, ...)
- Exit code indicates which specific check failed

**Example:**
```fortran
if (a%value /= 100) stop 1
if (.not. allocated(a%next)) stop 2
if (a%next%value /= 200) stop 3
```

**Alternative (less preferred):**
- Print/pattern matching with `! { dg-output "..." }`
- Use only when actual output values need verification
- More verbose and harder to maintain

### Reproducer Testing
PR-specific reproducers in `pr/<number>/`:
```bash
cd pr/<number>
make              # Build with custom gfortran
make run          # Execute
make clean        # Clean artifacts
```

## Patch Management

### Creating Patches
From inside `gcc/` on a topic branch:
```bash
git format-patch -1 HEAD -o ../pr/<number>/
```

### Topic Branch Naming
Use format: `pr<number>-<short-desc>`
- Example: `pr90519-finalizer-ice`
- Example: `pr121628-deep-copy-fix`

### Rebasing Before Patch Export
```bash
git -C gcc fetch origin
git -C gcc rebase origin/master
```

### Complete Patch Development Workflow

**CRITICAL: Always maintain a single, clean commit on top of upstream base branch.**

This workflow ensures patches are ready for upstream submission:

1. **Create Topic Branch**
   ```bash
   git -C gcc checkout -b pr<number>-<short-desc>
   ```

2. **Develop and Test Iteratively**
   - Make changes to source and test files
   - Build: `cd gcc-build && make -j32`
   - Test: `cd gcc-build/gcc && make -j32 -k check-gfortran`
   - Amend commits as you iterate: `git -C gcc commit --amend`

3. **Keep Single Commit with --amend**
   ```bash
   # After each round of changes:
   git -C gcc add <modified-files>
   git -C gcc commit --amend --no-edit  # Keeps same message
   # OR
   git -C gcc commit --amend  # Edit message
   ```

4. **Squash Multiple Commits if Needed**
   ```bash
   # If you accidentally created multiple commits:
   git -C gcc reset --soft HEAD~2  # Soft reset last 2 commits
   git -C gcc commit -s  # Create single commit
   ```

5. **Verify Commit Message Format**
   ```bash
   # Check TAB formatting (should show ^I):
   git -C gcc log -1 --format=%B | cat -A

   # Verify single commit on top of upstream:
   git -C gcc log --oneline -5
   ```

6. **Export Patch**
   ```bash
   git -C gcc format-patch -1 HEAD -o ../pr/<number>/
   ```

7. **Track in Meta-Repo**
   ```bash
   git add pr/<number>/<patch-file>
   git commit -m "pr<number>: description of patch"
   ```

**Key Principles:**
- ✅ ONE commit per PR on topic branch
- ✅ Commit message includes PR reference and ChangeLog
- ✅ ChangeLog entries ONLY in commit message (NOT in files)
- ✅ TAB formatting verified with `cat -A`
- ✅ Signed-off-by line present
- ✅ Tests passing before patch export
- ❌ NEVER push to upstream remote
- ❌ NEVER edit ChangeLog files directly

### GNU Commit Message Template with Sign-off

**Commit Message Format:**
```
<component>: <short summary (max 50 chars)>

<detailed description>

<issue/PR references>

Signed-off-by: Name <email@example.com>
```

**Rules:**
- Component: e.g., `fortran`, `libgfortran`, `testsuite`
- Short summary: Present tense, no period at end
- Detailed description: Explain WHY not just WHAT
- Blank line between sections
- Sign-off line is MANDATORY for all GCC contributions
- Co-authored patches: Add `Co-authored-by:` before `Signed-off-by:`

**ChangeLog Entry Formatting (CRITICAL):**
- ChangeLog entries start with a single TAB character
- Continuation lines use a SINGLE TAB, NOT <TAB><SPACE><SPACE>
- Function names in parentheses followed by colon
- Indentation: <TAB> for first level, <TAB> for continuation (NOT <TAB><SPACE><SPACE>)
- **VERIFY WITH**: `git log -1 --format=%B | cat -A` (should show `^I` for TABs, no trailing spaces)
- GCC filters will REJECT commits with improper ChangeLog formatting

**Example Commit Message:**
```
fortran: Implement optional type spec for DO CONCURRENT

This patch adds support for the F2018 optional integer type specification
in DO CONCURRENT headers, allowing constructs like:

  do concurrent (integer :: i=1:10)

The implementation follows the same approach used for FORALL type specs,
creating shadow variables when the type spec differs from any outer scope
variable with the same name.

	PR fortran/96255

gcc/fortran/ChangeLog:

	* match.cc (match_forall_header): Add type-spec parsing.
	* resolve.cc (gfc_resolve_forall): Handle shadow variables.

Co-authored-by: Steve Kargl <sgk@troutmask.apl.washington.edu>
Signed-off-by: Christopher Albert <albert@tugraz.at>
```

**Creating Commits with Proper Authorship:**
```bash
# For commits authored by others (e.g., applying Jerry's patch):
git commit --author="Jerry DeLisle <jvdelisle@charter.net>" -m "commit message"

# For your own commits with sign-off:
git commit -s -m "commit message"

# The -s flag automatically adds your Signed-off-by line
```

## Coding Standards for GCC Development

### CRITICAL: C vs C++ Language Choice

**GCC IS TRANSITIONING FROM C++ TO C - FOLLOW THIS POLICY STRICTLY:**

1. **PREFER C (NOT C++) FOR ALL NEW CODE**
   - GCC codebase is moving away from C++ back to C
   - Use pure ISO C for new implementations
   - Avoid C++ STL containers (vector, map, hash_set, etc.)
   - Avoid C++ features (auto, lambdas, templates, classes, etc.)

2. **ONLY use C++ when:**
   - Modifying existing heavily C++ code where C would be inconsistent
   - The surrounding file/module is already predominantly C++
   - Converting C++ to C would require massive refactoring

3. **For data structures:**
   - ✅ Use C-style linked lists, arrays, hash tables
   - ✅ Keep it SIMPLE (KISS principle)
   - ❌ Do NOT implement complex hash maps in C
   - ❌ Do NOT use C++ STL containers
   - Example: Use simple stack-based linked list instead of `hash_set`

4. **When in doubt:**
   - Check what the surrounding code uses
   - If file is mixed, prefer C
   - If converting C++ to C, keep it simple and equivalent

### Code Quality Checks

**Mandatory before completion:**
```bash
./gcc/contrib/check_GNU_style.sh <modified-file>
```

Run on each file modified in `gcc/gcc/fortran/` or `gcc/libgfortran/`.

## PR Directory Organization

Each PR directory (`pr/<number>/`) contains:
- Reproducer programs (`.f90` files)
- Generated patches (`.patch` files)
- Documentation (`README.md`, analysis files)
- Makefile for building reproducers with multiple compilers

**Compiler Testing in PR Makefiles:**
- Custom gfortran: `../gcc-build/gcc/gfortran -B ../gcc-build/gcc`
- System gfortran: `/usr/bin/gfortran`
- LLVM Flang: `/usr/bin/flang-new`
- Intel ifx: `/opt/intel/oneapi/compiler/2025.2/bin/ifx` (source setvars.sh first)
- NVIDIA nvfortran: `/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran`
- LFortran: `lfortran`

**Example Makefile pattern:**
```makefile
FC_CUSTOM = ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
FC_SYSTEM = /usr/bin/gfortran
FC_FLANG  = /usr/bin/flang-new
FC_IFX    = /opt/intel/oneapi/compiler/2025.2/bin/ifx
FC_NVHPC  = /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran
FC_LFORT  = lfortran

FFLAGS = -Wa,--noexecstack -Wl,-z,noexecstack

all: test-custom test-system test-flang test-ifx test-nvhpc test-lfortran

test-custom:
	$(FC_CUSTOM) $(FFLAGS) reproducer.f90 -o reproducer-custom.x

test-system:
	$(FC_SYSTEM) $(FFLAGS) reproducer.f90 -o reproducer-system.x

test-flang:
	$(FC_FLANG) reproducer.f90 -o reproducer-flang.x

test-ifx:
	bash -c "source /opt/intel/oneapi/setvars.sh && $(FC_IFX) reproducer.f90 -o reproducer-ifx.x"

test-nvhpc:
	$(FC_NVHPC) reproducer.f90 -o reproducer-nvhpc.x

test-lfortran:
	@if command -v $(FC_LFORT) >/dev/null 2>&1; then \
		$(FC_LFORT) reproducer.f90 -o reproducer-lfortran.x; \
	else \
		echo "LFortran not found"; \
	fi

clean:
	rm -f *.x *.o *.mod *.smod
```

## Test Suite Execution Details

### Common Mistakes to Avoid
1. ❌ **WRONG**: Running from `gcc-build/` (no such target exists there)
2. ❌ **WRONG**: Running from `gcc/` source directory
3. ❌ **WRONG**: Running from meta-repo root
4. ✅ **CORRECT**: Running from `gcc-build/gcc/` ONLY
5. Not redirecting output to log file
6. Not waiting for completion before reading results

### Proper Execution Flow
1. Rebuild: `cd /home/ert/code/gcc-dev/gcc-build && make -j32`
2. Change to test directory: `cd /home/ert/code/gcc-dev/gcc-build/gcc`
3. Launch tests: `make -j32 -k check-gfortran > /tmp/test.log 2>&1 &`
4. Monitor: Check `/tmp/test.log` or use BashOutput tool
5. Wait: Test suite takes ~20-30 minutes to complete
6. Results: `grep "# of" /home/ert/code/gcc-dev/gcc-build/gcc/testsuite/gfortran/gfortran.sum`

### Quick Test Commands
```bash
# Full test suite from correct directory:
cd /home/ert/code/gcc-dev/gcc-build/gcc && make -j32 -k check-gfortran

# Single test:
cd /home/ert/code/gcc-dev/gcc-build/gcc && make check-gfortran RUNTESTFLAGS="finalize_45.f90"

# Specific test group:
cd /home/ert/code/gcc-dev/gcc-build/gcc && make check-gfortran RUNTESTFLAGS="dg.exp=finalize*.f90"
```

## 🚨 FORTRAN STANDARDS COMPLIANCE - ABSOLUTE REQUIREMENTS 🚨

**MANDATORY POLICY - ZERO TOLERANCE FOR NON-COMPLIANCE:**

### ISO Standard Compliance is NON-NEGOTIABLE
- **ALL implementations MUST match Fortran 2018 (or later) ISO standard EXACTLY**
- **NO EXCEPTIONS** for "partial implementations" or "known limitations"
- **NO "acceptable for now"** - non-compliance is a BUG that MUST be fixed
- **ALWAYS document standard violations** with specific ISO section references
- **ALWAYS mark non-compliant behavior** as ❌ NOT ACCEPTABLE in documentation
- **ALWAYS compare against reference compilers** (Intel ifx, NVIDIA nvfortran) for correct behavior

### Standards Compliance Validation Protocol
1. **Identify ISO Standard Reference**: Cite exact section (e.g., F2018 7.5.6.3)
2. **Test Reference Compilers**: Intel ifx, NVIDIA nvfortran (known for compliance)
3. **Document Expected Behavior**: What ISO standard requires
4. **Document Actual Behavior**: What GCC currently does
5. **Mark Compliance Status**:
   - ✅ **STANDARD-COMPLIANT**: Matches ISO standard exactly
   - ❌ **NON-COMPLIANT**: Violates ISO standard - MUST BE FIXED
6. **NO Compromise**: Never accept partial compliance as "good enough"

### Allocatable Component Assignment (Fortran 2018)
- Component-by-component intrinsic assignment
- Allocatable LHS components: deallocate first, reallocate to match RHS, then copy
- Must produce distinct storage (no aliasing with source)
- Deep copy required for nested allocatable components
- **Reference**: ISO/IEC 1539-1:2018 Section 7.5.2.3

### Finalization (Fortran 2018)
- FINAL procedures called when derived type objects go out of scope
- Function results MUST be finalized after assignment (F2018 7.5.6.3)
- Self-assignment (`a = a`) requires special handling to avoid use-after-free
- Parenthesized expressions like `(a)` create INTRINSIC_PARENTHESES operator nodes
- Finalizer wrappers must not create self-referencing result symbols
- **Reference**: ISO/IEC 1539-1:2018 Section 7.5.6.3

### Common Expression Tree Patterns in trans-expr.cc
- **INTRINSIC_PARENTHESES**: Created by `(expr)` - defeats simple variable checks
- Use helper functions to strip parentheses when checking for self-assignment
- Check both `gfc_dep_compare_expr` (compile-time) and runtime pointer equality
- `gfc_expr_is_variable(expr)` returns false for parenthesized variables
- Always strip parentheses before enabling `deep_copy` flag in assignments

## Debugging and Validation Techniques

### Multi-Compiler Validation Strategy - MANDATORY FOR ALL FIXES

**CRITICAL: ALL bug fixes MUST be validated against ISO standard behavior:**

1. **Identify Reference Implementation (MANDATORY):**
   - **ALWAYS test with Intel ifx and NVIDIA nvfortran** (best F2018+ compliance)
   - Test with LLVM Flang and LFortran when available
   - Document which compilers show ISO-compliant behavior
   - **Reference compilers are the source of truth**, not GCC current behavior

2. **Create Minimal Reproducer:**
   - Strip down to smallest test case showing the bug
   - Test both simple (`a = a`) and parenthesized (`a = (a)`) cases
   - Use if/stop pattern for clear pass/fail indication

3. **Document ISO Standard Requirements:**
   - Cite exact ISO standard section (e.g., ISO/IEC 1539-1:2018 Section 7.5.6.3)
   - Document what standard REQUIRES (not what GCC currently does)
   - Mark any deviation from standard as ❌ NON-COMPLIANT

4. **Trace Execution Path:**
   - Add temporary debug output in trans-expr.cc to trace code paths
   - Check which flags are set (deep_copy, finalize, etc.)
   - Verify expression tree structure (EXPR_VARIABLE vs EXPR_OP)

5. **Verify Fix Completeness (STRICT):**
   - Test all related expression patterns
   - Run full test suite to catch regressions
   - **MANDATORY**: Compare behavior with reference compilers
   - **MANDATORY**: Match ISO standard exactly - NO partial compliance
   - If fix doesn't achieve full compliance, document as ❌ INCOMPLETE

### Commit Message Verification
Before finalizing commits:
```bash
# Check ChangeLog formatting (should show ^I for TABs):
git log -1 --format=%B | cat -A

# Verify commit compiles and tests pass:
cd /home/ert/code/gcc-dev/gcc-build && make -j32
cd /home/ert/code/gcc-dev/gcc-build/gcc && make -j32 -k check-gfortran

# Run style checker:
./gcc/contrib/check_GNU_style.sh gcc/fortran/<modified-file>
```

## Upstream Submission Policy

### 🚨 CRITICAL: NEVER Submit Patches Without Explicit User Permission

**ABSOLUTE PROHIBITION - ZERO TOLERANCE:**
- **NEVER send emails to GCC mailing lists** (fortran@gcc.gnu.org, gcc-patches@gcc.gnu.org)
- **NEVER post patches to GCC Bugzilla** without explicit user instruction
- **NEVER create pull requests or submissions** to any GCC upstream channels
- **ALWAYS prepare patches** and get user approval before ANY upstream interaction

**Permitted Actions:**
- ✅ Prepare patch files with `git format-patch`
- ✅ Generate commit messages with proper ChangeLog format
- ✅ Run local tests and validation
- ✅ Export patches to `pr/<number>/` directory
- ✅ Document submission readiness

**Requiring Explicit User Permission:**
- ❌ Posting to mailing lists
- ❌ Updating Bugzilla
- ❌ Any external communication about patches
- ❌ Sending emails on behalf of the user

**Rationale:**
- User controls timing and content of all upstream submissions
- User owns the relationship with GCC community
- User determines when patches are ready for public review
- User handles any required legal/authorization processes

## Meta-Repository Commits

Track documentation, reproducer updates, and organizational changes in the meta-repo:
```bash
git add pr/ CLAUDE.md <files>
git commit -m "description"
git push origin main
```

Keep meta-repo commits separate from GCC upstream patches.
