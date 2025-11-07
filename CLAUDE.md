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
   - **NOT currently installed**
   - Interactive Fortran compiler
   - Install if needed for additional validation

**Testing Protocol:**
- Always test reproducers with at least 2-3 compilers
- Document which compilers show the bug
- Document which compilers show correct behavior
- Compare output for semantic correctness

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

**Example Makefile pattern:**
```makefile
FC_CUSTOM = ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
FC_SYSTEM = /usr/bin/gfortran
FC_FLANG  = /usr/bin/flang-new
FC_IFX    = /opt/intel/oneapi/compiler/2025.2/bin/ifx
FC_NVHPC  = /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran

FFLAGS = -Wa,--noexecstack -Wl,-z,noexecstack

all: test-custom test-system test-flang test-ifx test-nvhpc

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

clean:
	rm -f *.x *.o *.mod
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
