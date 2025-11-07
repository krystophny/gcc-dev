# GCC Fortran Bug Reproducers

This directory contains minimal reproducers for GCC Fortran bugs, primarily focusing on internal compiler errors related to finalizers, allocatable components, parameterized derived types, and coarrays.

## Purpose

Track and test GCC Fortran compiler regressions across multiple compiler versions:
- System gfortran 15.2.1
- Development gfortran 16.0 (local build)
- Intel ifx 2025.2.1 (reference implementation)

Each subdirectory contains a minimal reproducer, test results, and analysis for a specific bug report from GCC Bugzilla.

## Status Summary

| PR | Title | Bugzilla Status | System GCC 15.2.1 | Dev GCC 16.0 | Intel ifx 2025.2.1 | Category |
|----|-------|----------------|-------------------|--------------|-------------------|----------|
| [90519](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=90519) | FINAL + recursive allocatable ICE | NEW | ICE | PASS | PASS | Finalizer |
| [121472](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472) | ICE with constructor and finalizer | UNCONFIRMED | ICE | ICE | PASS | Finalizer |
| [121628](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121628) | Recursive allocatable deep copy | NEW | - | - | PASS | Allocatable |
| [113885](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=113885) | ICE with finalization and elemental functions | RESOLVED FIXED | PASS | PASS | PASS | Finalizer |
| [114535](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=114535) | ICE with elemental finalizer | RESOLVED FIXED | PASS | PASS | PASS | Finalizer |
| [110987](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110987) | Segfault with finalization of temporary | RESOLVED FIXED | PASS | PASS | PASS | Finalizer |
| [82622](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82622) | ICE with PDT allocation | RESOLVED FIXED | PASS | PASS | PASS | PDT |
| [116669](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=116669) | Crash on circular derived type | RESOLVED FIXED | PASS | PASS | PASS | Type Resolution |
| [85002](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85002) | Coarray ICE in fold_ternary_loc | RESOLVED FIXED | PASS | PASS | FAIL* | Coarray |
| [104684](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=104684) | Coarray ICE in verify_gimple | RESOLVED FIXED | PASS | PASS | FAIL* | Coarray |
| [103716](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103716) | ICE with character len inquiry | RESOLVED FIXED | PASS | PASS | PASS | Character |
| [103368](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103368) | ICE with class(*) in structure constructor | RESOLVED FIXED | PASS | PASS | PASS | Polymorphic |
| [122191](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122191) | ICE with composite PDT result | RESOLVED FIXED | PASS | PASS | PASS | PDT |

*Coarray tests expected to fail on ifx - different implementation than gfortran's `-fcoarray=single`

## Analysis

### Active Bugs

**PR121472** - ICE with constructor and finalizer
- Status: UNCONFIRMED (Bugzilla), ACTIVE (both compilers fail)
- System GCC 15.2.1: ICE in gimplify_expr at gimplify.cc:20443
- Dev GCC 16.0: ICE in gimplify_expr at gimplify.cc:21278
- Priority: HIGH - affects both released and development versions

### Fixed in Development (Not Yet Released)

**PR90519** - FINAL + recursive allocatable ICE
- Status: NEW (Bugzilla), FIXED (dev compiler only)
- System GCC 15.2.1: ICE
- Dev GCC 16.0: PASS
- Fix: Local patch generates distinct result symbols for FINAL wrappers
- Release target: GCC 16.1 (projected April 2026)

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
make 121472
make 90519

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
