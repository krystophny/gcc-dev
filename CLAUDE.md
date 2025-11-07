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
- **Never push the `gcc/` repository** - Export patches instead
- **Do not edit GCC ChangeLog files** - Upstream regenerates them from commits

## Build and Test Workflow

### Building GCC
```bash
cd gcc-build
make -j32
```

### Running Test Suite
**CRITICAL: Always use background shell execution for test suites**

**Correct workflow:**
```bash
cd gcc-build/gcc
make -j32 check-gfortran > /tmp/test-output.log 2>&1 &
```
Use Bash tool with `run_in_background: true` parameter.

**Test results location:**
- Summary: `gcc-build/gcc/testsuite/gfortran/gfortran.sum`
- Detailed log: `gcc-build/gcc/testsuite/gfortran/gfortran.log`
- Look for: `# of expected passes`, `# of unexpected failures`

**Verification checklist:**
- Zero unexpected failures
- All new tests passing
- No regressions in existing tests

### Custom Compiler Invocation
```bash
gcc-build/gcc/gfortran -B gcc-build/gcc <file.f90>
```

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

## Code Quality Checks

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
- Makefile for building reproducers

**Reference compilers:**
- Custom gfortran: `../gcc-build/gcc/gfortran -B ../gcc-build/gcc`
- Intel ifx: Source `/opt/intel/oneapi/setvars.sh` first

## Test Suite Execution Details

### Common Mistakes to Avoid
1. Running `make check-gfortran` from build root (no such target)
2. Using shell `&` operator within Bash commands
3. Running from wrong directory (must be in `gcc-build/gcc/`)
4. Not redirecting output to log file
5. Not waiting for completion before reading results

### Proper Execution Flow
1. Rebuild: `cd gcc-build && make -j32`
2. Launch tests: `cd gcc && make -j32 check-gfortran > /tmp/test.log 2>&1` (background shell)
3. Monitor: Use BashOutput tool to check status
4. Wait: Check shell status until "completed"
5. Results: `grep "# of" gcc-build/gcc/testsuite/gfortran/gfortran.sum`

## Fortran Standards Compliance

### Allocatable Component Assignment (Fortran 2018)
- Component-by-component intrinsic assignment
- Allocatable LHS components: deallocate first, reallocate to match RHS, then copy
- Must produce distinct storage (no aliasing with source)
- Deep copy required for nested allocatable components

### Finalization
- FINAL procedures called when derived type objects go out of scope
- Self-assignment (`a = a`) requires special handling to avoid use-after-free
- Finalizer wrappers must not create self-referencing result symbols

## Meta-Repository Commits

Track documentation, reproducer updates, and organizational changes in the meta-repo:
```bash
git add pr/ CLAUDE.md <files>
git commit -m "description"
git push origin main
```

Keep meta-repo commits separate from GCC upstream patches.
