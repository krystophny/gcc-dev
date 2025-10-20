# GCC Development Guidelines

## 🚨 HARD RULE: GCC Coding Standards Compliance
**MANDATORY REQUIREMENT**: ALL code MUST strictly comply with GNU coding standards. NO exceptions.

- **C/C++**: 2-space indentation, braces on separate lines, 80-column limit
- **Fortran**: 4-space indentation, 88-column wrapping, `implicit none`
- **Style Validation**: Run `python3 gcc/contrib/check_GNU_style.py <patch-file>` before ALL commits
- **Fix EVERY reported style issue** - no tolerance for violations
- **Reference**: https://gcc.gnu.org/codingconventions.html

## Project Structure
- **Source**: `gcc/` (tracked), `gcc-build/` (disposable build output)
- **Core Work**: `gcc/gcc/` (compiler), `gcc/libgfortran/` (runtime), `gcc/libquadmath/` (math)
- **Tests**: `gcc/gcc/testsuite/gfortran.dg/` (descriptive `*.f90`)
- **Reproducers**: `bugs/` (minimal cases, investigation docs)

## Git Workflow
- **Operations**: Inside `gcc/` only (clean history)
- **Building**: In `gcc-build/` using `make -C gcc-build ... -j32`
- **Documentation**: Update `bugs/ALLOCATABLE_DEEPCOPY_PLAYBOOK.md` with progress


## Build Commands
- **Bootstrap**: `./bootstrap.sh` (reconfigures with defaults, re-run after configure changes)
- **Build**: `make -C gcc-build -j$(nproc) all-gfortran`
- **Test**: `make -C gcc-build check-gfortran RUNTESTFLAGS="--target_board=unix/-O0"`
- **Test Summary**: `python3 gcc/contrib/test_summary gcc-build/gcc/testsuite/*.sum`
- **Install**: `make -C gcc-build install-gfortran DESTDIR=$PWD/stage`

## Fortran-Specific Standards
- **Precision**: `use, intrinsic :: iso_fortran_env, only: dp => real64`, declare as `real(dp)`
- **Naming**: Derived types `<name>_t`, functions `gfc_*` or `gfortran_*`
- **Formatting**: `implicit none`, proper `intent` declarations, 4-space indentation
- **Style**: 88-column wrapping, avoid pointers unless required, prefer `allocatable`

## Testing Requirements
- **Format**: `dg-do run` or `dg-do compile` directives, minimal and self-checking
- **Grouping**: Related scenarios in same `.exp` entry
- **Regression**: Archive failing source in `bugs/`, reference in commit
- **Coverage**: At least one positive and one negative test per feature
- **Results**: Attach `.sum` excerpt or `test_summary` output

## Commit Standards
- **Format**: `component: imperative summary` (e.g., `gfortran: fix polymorphic deep copy`)
- **Scope**: Small, single-subsystem commits
- **Staging**: Explicit `git add path/to/file` only
- **Validation**: `make -C gcc-build check-gfortran` must pass before PR
- **Content**: Link Bugzilla ID, describe root cause, detail fix, note follow-up
- **Evidence**: Attach logs, not screenshots
- **Merge**: Only after reviewer approval and CI success
