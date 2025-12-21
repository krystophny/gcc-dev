# GCC Fortran Bug Reproducers

This directory contains minimal reproducers for GCC Fortran bugs, primarily focusing on internal compiler errors related to finalizers, allocatable components, parameterized derived types, and coarrays.

## Purpose

Track and test GCC Fortran compiler regressions across multiple compiler versions:
- System gfortran 15.2.1
- Development gfortran 16.0 (local build)
- Intel ifx 2025.2.1 (reference implementation)

Each subdirectory contains a minimal reproducer, test results, and analysis for a specific bug report from GCC Bugzilla.

## Status Summary

### Open PRs

| PR | Title | Local Status | Notes |
|----|-------|--------------|-------|
| [102430](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102430) | OpenMP `linear` on arrays ICE / missing support | SUBMITTED | Patch exported to `pr/102430/` and pushed to GCC fork branch `pr102430-linear-sorry`. |
| [107721](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107721) | Array constructor type-spec lost when parenthesized | READY FOR SUBMISSION | Patch `0001-fortran-honor-array-constructor-type-spec-during-fol.patch` passes local matrix; awaiting upstream posting (see `pr/107721/`). |
| [121472](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472) | Constructor/finalizer ICE | OPEN | ICE in `gimplify_expr` on GCC 15.2.1 and trunk; repro + patch tracked in `pr/121472/`. |

### Completed PRs

| PR | Title | Resolution | Evidence |
|----|-------|------------|----------|
| [32365](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=32365) | Better specification-statement diagnostics | Merged upstream (commit 7db49bf4be2, 2025-11-17). | New test `gfortran.dg/spec_statement_in_exec.f90` added; see `pr/32365/README.md`. |
| [90519](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=90519) | FINAL + recursive allocatable ICE | Merged upstream (commit 1eb696fc092, 2025-11-07). | Finalizer wrapper now uses separate result symbol; tests added (`finalizer_recursive_alloc_*.f90`, `finalizer_self_assign.f90`). Details in `pr/90519/README.md`. |
| [121628](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121628) | Recursive allocatable deep copy | Upstream fix in GCC r16-5094. | Dev gfortran compile of `pr/121628/deepcopy.f90` succeeded (2025-11-13); details in `pr/121628/README.md`. |
| [96255](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96255) | DO CONCURRENT type-spec implementation | Merged upstream (commits 5e62a23cc3a & 1099ffffffe). | Dev gfortran compile of `pr/96255/looper.f90` succeeded (2025-11-13); see `pr/96255/README.md`. |

*Coarray tests are still expected to fail on ifx because it lacks gfortran's `-fcoarray=single` semantics.*

## Analysis

### Active Bugs

**PR102430** - OpenMP `linear` clause on arrays
- Status: SUBMITTED
- GCC accepted `linear(a)` with `a` an array on `parallel do`, but the OpenMP
  worksharing-loop lowering historically did not implement array-linear, leading
  to an ICE during OpenMP expansion. See `pr/102430/` for reproducer and notes.
- Tracking issue: https://github.com/krystophny/gcc-dev/issues/9

**PR107721** - Array constructor type-spec lost with parentheses
- Status: READY FOR UPSTREAM (Bugzilla still open)
- Both system GCC 15.2.1 and trunk fold parenthesized constructors without converting elements to the declared type; reference compilers (ifx, nvfortran, flang-new) are correct.
- Patch converts constructor elements before folding and adds comprehensive regression (`array_constructor_typespec_1.f90`).
- Action: post patch from `pr/107721/0001-fortran-honor-array-constructor-type-spec-during-fol.patch` to gcc-patches.

**PR121472** - ICE with constructor and finalizer
- Status: UNCONFIRMED (Bugzilla), ACTIVE (both compilers fail)
- System GCC 15.2.1: ICE in gimplify_expr at gimplify.cc:20443
- Dev GCC 16.0: ICE in gimplify_expr at gimplify.cc:21278
- Priority: HIGH - affects both released and development versions; reproducer + logging available in `pr/121472/`.

### Completed Bugs

**PR32365** - Specification-statement diagnostics
- Status: MERGED UPSTREAM (commit 7db49bf4be2, 2025-11-17)
- Fix: `parse_executable` now rejects late spec/OpenMP statements unconditionally; new regression `spec_statement_in_exec.f90` exercises DATA/COMMON/NAMELIST/OpenMP cases with `-fopenmp`.

**PR90519** - FINAL + recursive allocatable ICE
- Status: MERGED UPSTREAM (commit 1eb696fc092, 2025-11-07)
- Fix: FINAL wrappers now use distinct result symbols and parenthesized self-assignment is detected via `strip_parentheses`, preventing ICE and use-after-free. Regression suite includes `finalizer_recursive_alloc_{1,2}.f90` and `finalizer_self_assign.f90`.

**PR121628** - Recursive allocatable deep copy
- Status: MERGED UPSTREAM (GCC r16-5094)
- Fix: Runtime deep-copy helper plus compiler integration now shipped on trunk; reproducer builds cleanly (see `pr/121628/README.md`).

**PR96255** - DO CONCURRENT type-spec implementation
- Status: MERGED UPSTREAM (commits 5e62a23cc3a & 1099ffffffe)
- Fix: Optional type-spec parsing and iterator-marking logic; `pr/96255/looper.f90` compiles with current trunk build.

### Fixed but Bugzilla Shows Open

None currently - all resolved bugs have been properly closed in Bugzilla.

### Fixed and Closed

The following bugs are marked RESOLVED FIXED in Bugzilla and pass in both compiler versions:
- **PR113885** - Finalization block placement (fixed GCC 15+)
- **PR114535** - Elemental finalizer across modules (fixed GCC 15+)
- **PR110987** - Segfault with temporary finalization (fixed GCC 14+)
- **PR82622** - PDT allocation null pointer (fixed in modern GCC)
- **PR116669** - Circular derived type detection (fixed GCC 15+, Jan 2025)
- **PR85002** - Coarray deep copy (fixed GCC 16+, Sep 2024)
- **PR104684** - Coarray gimple verification (fixed GCC 16+)
- **PR103716** - Character length inquiry (fixed GCC 14+)
- **PR103368** - Class(*) structure constructor (fixed GCC 14+)
- **PR122191** - PDT interface body (fixed Oct 2025)

## Usage

### Test All Bugs

```bash
# Test with system compiler
make test-system

# Test with development compiler
make test-dev

# Test with Intel ifx
make test-ifx

# Test with all compilers
make test-all
```

### Test Specific Bug

```bash
# Test individual PR
make 107721
make 121472

# Test by number
make <PR-number>
```

### View Summary

```bash
make summary
```

### Clean Build Artifacts

```bash
make clean
```

## Special Compilation Requirements

### Coarray Features

PRs 85002 and 104684 require `-fcoarray=single` flag. The Makefile automatically applies this flag for these specific bugs.

### Custom Compiler Build

Development compiler tests use:
- Compiler: `/home/ert/code/gcc-dev/gcc-build/gcc/gfortran`
- Flags: `-B` for driver, `-L` and `-Wl,-rpath` for libgfortran
- Security: `-Wa,--noexecstack -Wl,-z,noexecstack`

## Directory Structure

Each PR subdirectory contains:
- `reproducer.f90` or `<name>.f90` - Minimal test case that triggers the bug
- `README.md` - Bug description, Bugzilla status, test results, fix details
- `*.patch` - Fix patches (where applicable)
- `*.o`, `*.x` - Compiled artifacts (not tracked)

### Example: pr/90519/
```
90519/
├── finalizer_min.f90              # Minimal reproducer
├── 0001-fortran-Fix-ICE-*.patch   # Proposed fix
└── README.md                      # Full analysis and fix plan
```

## Adding New Reproducers

1. Create subdirectory named `<PR-number>/`
2. Add minimal Fortran reproducer as `reproducer.f90`
3. Create `README.md` with:
   - Bug URL
   - Bugzilla status
   - Bug description
   - Expected vs actual behavior
   - Test results (system/dev/intel)
   - Fix details (if known)
4. Update `PR_DIRS` in top-level `Makefile`
5. Add coarray flag to `COARRAY_PRS` if needed
6. Test with `make <PR-number>`

## Test Result Interpretation

- **PASS** - Compilation succeeds without errors
- **ICE** - Internal compiler error detected
- **FAIL** - Compilation fails with error messages (not ICE)
- **SKIP** - Test not run (missing compiler, no reproducer)

## Compiler Versions

### System gfortran
```
GNU Fortran (GCC) 15.2.1 20250405
```

### Dev gfortran
```
GNU Fortran (GCC) 16.0.0 20251107 (experimental)
Location: /home/ert/code/gcc-dev/gcc-build/gcc/gfortran
```

### Intel ifx
```
Intel(R) Fortran Compiler 2025.2.1 (2025.2.1.20251128)
```

Note: Intel ifx does not support `-fcoarray=single` the same way as gfortran, so coarray tests (PR85002, PR104684) fail as expected.

## Related Documentation

- `/home/ert/code/gcc-dev/CLAUDE.md` - AI agent analysis methodology
- `/home/ert/code/gcc-dev/pr/121628/ALLOCATABLE_DEEPCOPY_PLAYBOOK.md` - Deep copy analysis
- `/home/ert/code/gcc-dev/gcc/` - Upstream GCC repository (local clone)

## Notes

- Do not push the `gcc/` repository - export patches instead
- Do not edit GCC ChangeLog files - maintainers regenerate from commits
- Run `./gcc/contrib/check_GNU_style.sh` on modified GCC sources
- All paths in commands should be absolute from repo root
- Stack protection flags required for all test compilations

## Test Automation

The top-level Makefile provides parallel testing infrastructure:
- Sequential testing of each PR
- Automatic ICE detection via log parsing
- Conditional coarray flag application
- Compiler availability checking
- Temporary file isolation in `/tmp/`

## Bug Categories

### Finalizer Issues (6 PRs)
Bugs related to FINAL procedures, wrapper generation, and cleanup timing.

### Allocatable Components (2 PRs)
Deep copy semantics for recursive allocatable structures.

### Parameterized Derived Types (2 PRs)
PDT allocation, interface bodies, and component handling.

### Coarray Features (2 PRs)
Parallel programming constructs with allocatable components.

### Type Resolution (1 PR)
Circular dependency detection in derived types.

### Character Handling (1 PR)
Length inquiry for assumed-length arrays.

### Polymorphic Types (1 PR)
Class(*) unlimited polymorphic components.
