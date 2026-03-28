# GCC Fortran Bug Reproducers

Minimal reproducers and patches for GCC Fortran and libgomp bugs.

## Pending Patches (on fork, awaiting upstream)

| PR | Title | GitHub Issue |
|----|-------|--------------|
| [102430](102430/) | OpenMP linear(array) ICE | [#9](https://github.com/krystophny/gcc-dev/issues/9) |
| [102333](102333/) | Invalid `PROCEDURE` statement accepted | [#78](https://github.com/krystophny/gcc-dev/issues/78) |
| [103276](103276/) | OpenACC ENTER DATA duplicate mapping | [#10](https://github.com/krystophny/gcc-dev/issues/10) |
| [120723](120723/) | OpenACC `attach(scalar)` ICE | [#96](https://github.com/krystophny/gcc-dev/issues/96) |
| [123252](123252/) | OpenACC scalar member wrong value | [#11](https://github.com/krystophny/gcc-dev/issues/11) |
| [123280](123280/) | acc_is_present fails for assumed-shape | [#12](https://github.com/krystophny/gcc-dev/issues/12) |
| [96080](96080/) | acc_is_present fails for pointers | [#13](https://github.com/krystophny/gcc-dev/issues/13) |
| [123282](123282/) | OpenACC refcount bug in repeated alloc/dealloc cycles | [#14](https://github.com/krystophny/gcc-dev/issues/14) |

## Open Tracking (no patch yet)

| PR | Title | GitHub Issue |
|----|-------|--------------|
| 42954 | TARGET_*_CPP_BUILTINS missing | [#52](https://github.com/krystophny/gcc-dev/issues/52) |
| 60576 | assumed_rank_7.f90 failure | [#53](https://github.com/krystophny/gcc-dev/issues/53) |
| 79524 | Valgrind/ASan error in `fimplicit_none_2.f90` | [#55](https://github.com/krystophny/gcc-dev/issues/55) |
| 101760 | Deferred-length char + OMP target ICE | [#76](https://github.com/krystophny/gcc-dev/issues/76) |
| 109788 | UB shift exponent 64 in IPA/Fortran path | [#91](https://github.com/krystophny/gcc-dev/issues/91) |
| 110626 | Duplicated finalization in derived assignment | [#92](https://github.com/krystophny/gcc-dev/issues/92) |

## Merged Upstream

| PR | Title | GCC Commit | GitHub Issue |
|----|-------|------------|--------------|
| [32365](32365/) | Spec-statement diagnostics | 7db49bf4be2 | [#3](https://github.com/krystophny/gcc-dev/issues/3) |
| [82721](82721/) | CHARACTER duplicate declaration ICE | 5cfaad50af7 | [#56](https://github.com/krystophny/gcc-dev/issues/56) |
| [90519](90519/) | FINAL + recursive allocatable ICE | 1eb696fc092 | [#4](https://github.com/krystophny/gcc-dev/issues/4) |
| [92613](92613/) | -cpp -fpreprocessed warning | 15ffee4e129 | [#7](https://github.com/krystophny/gcc-dev/issues/7) |
| [95338](95338/) | ENTRY + `-ff2c` ICE | 490c7ba8d880 | [#68](https://github.com/krystophny/gcc-dev/issues/68) |
| [96255](96255/) | DO CONCURRENT type-spec | 5e62a23cc3a | [#1](https://github.com/krystophny/gcc-dev/issues/1) |
| [102459](102459/) | OMP iterator component array ICE | d2ab04fbba7b | [#79](https://github.com/krystophny/gcc-dev/issues/79) |
| [102596](102596/) | OMP task reduction ctor ICE | e53a7510be51 | [#80](https://github.com/krystophny/gcc-dev/issues/80) |
| [106946](106946/) | ICE on invalid CLASS component in derived type | 0d0fbb0a01e4 | [#88](https://github.com/krystophny/gcc-dev/issues/88) |
| [107721](107721/) | Array constructor type-spec | c50d263beff | [#6](https://github.com/krystophny/gcc-dev/issues/6) |
| [110877](110877/) | Polymorphic dummy assignment drops alloc comps | b018656f8c01 | [#101](https://github.com/krystophny/gcc-dev/issues/101) |
| [120286](120286/) | OpenMP polymorphic pointer privatization | 60fbabc1a182 | [#95](https://github.com/krystophny/gcc-dev/issues/95) |
| [121472](121472/) | Constructor/finalizer ICE | 5bb465a7896 | [#2](https://github.com/krystophny/gcc-dev/issues/2) |
| [121475](121475/) | Function result finalization | a30b5f23b58 | [#8](https://github.com/krystophny/gcc-dev/issues/8) |
| [121628](121628/) | Recursive allocatable deep copy | a1fe2cfa896 | [#5](https://github.com/krystophny/gcc-dev/issues/5) |
| [122491](122491/) | Missing END BLOCK recovery UAF | ff2f6c5153e | [#50](https://github.com/krystophny/gcc-dev/issues/50) |
| [123868](123868/) | Nested allocatable assignment leak | ca448bc5e43 | [#47](https://github.com/krystophny/gcc-dev/issues/47) |
| [123947](123947/) | Recursive deep-copy helper generation | e0b70284cfa / 83ef3db4b38 | [#48](https://github.com/krystophny/gcc-dev/issues/48) |
| [123949](123949/) | PDT ICE with large KIND values | 3a17cc11cb5 / 33b945b4e63 | [#49](https://github.com/krystophny/gcc-dev/issues/49) |
| [124208](124208/) | Iterator counting in nested block scopes | 97965bdc1ed | [#100](https://github.com/krystophny/gcc-dev/issues/100) |
| [124235](124235/) | ALLOCATE sub-object recursive-type ICE | e0b70284cfa | [#51](https://github.com/krystophny/gcc-dev/issues/51) |
| [124482](124482/) | CLASS component error-recovery regression on Solaris/SPARC | d8b00bf2e151 | [#102](https://github.com/krystophny/gcc-dev/issues/102) |

## Directory Structure

Each PR directory contains:

```
pr/<number>/
├── README.md           # Links, status, analysis
├── status.json         # Canonical machine-readable status/backport metadata
├── reproducer.f90      # Minimal test case
├── 0001-*.patch        # Exported patch (if applicable)
├── submission/         # Generated maintainer/Bugzilla/mail packets
├── backports/          # Branch-specific patch and status packets
└── Makefile            # Optional multi-compiler testing
```

Top-level generated backport status:

```
pr/backport-matrix.md
pr/backport-matrix.json
```

Manual regression status summary:

```
pr/regression-status.md
pr/bugzilla-review-pending.md
```

## Usage

```bash
# Test specific PR with dev compiler
cd pr/123280 && make test-dev

# Test all PRs
make test-all
```

## Adding New Reproducers

1. Create `pr/<number>/`
2. Add `reproducer.f90` (minimal test case)
3. Add `README.md` with links and analysis
4. Test with reference compilers (nvfortran for OpenACC)
5. Export patch: `git -C ../gcc format-patch -1 HEAD -o .`
6. Refresh structured metadata: `python3 scripts/gcc-workflow.py sync-metadata <number>`
7. Regenerate maintainer packet: `python3 scripts/gcc-workflow.py render-packet <number>`

## Backport Commands

```bash
# Refresh metadata for every tracked PR
python3 scripts/gcc-workflow.py sync-metadata --all

# Render packets for every regression PR
python3 scripts/gcc-workflow.py render-packet --all --regressions

# Record branch applicability for active maintained release branches
python3 scripts/gcc-workflow.py branch-check --branches gcc-15,gcc-14,gcc-13
```

## Links

- [GCC Bugzilla](https://gcc.gnu.org/bugzilla/)
- [GitHub Issues](https://github.com/krystophny/gcc-dev/issues)
- [Development Guide](../CLAUDE.md)
