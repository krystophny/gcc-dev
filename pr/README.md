# GCC Fortran Bug Reproducers

Minimal reproducers and patches for GCC Fortran and libgomp bugs.

## Pending Patches (on fork, awaiting upstream)

| PR | Title | GitHub Issue |
|----|-------|--------------|
| [102430](102430/) | OpenMP linear(array) ICE | [#9](https://github.com/krystophny/gcc-dev/issues/9) |
| [103276](103276/) | OpenACC ENTER DATA duplicate mapping | [#10](https://github.com/krystophny/gcc-dev/issues/10) |
| [123252](123252/) | OpenACC scalar member wrong value | [#11](https://github.com/krystophny/gcc-dev/issues/11) |
| [123280](123280/) | acc_is_present fails for assumed-shape | [#12](https://github.com/krystophny/gcc-dev/issues/12) |
| [96080](96080/) | acc_is_present fails for pointers | [#13](https://github.com/krystophny/gcc-dev/issues/13) |

## Merged Upstream

| PR | Title | GCC Commit | GitHub Issue |
|----|-------|------------|--------------|
| [32365](32365/) | Spec-statement diagnostics | 7db49bf4be2 | [#3](https://github.com/krystophny/gcc-dev/issues/3) |
| [90519](90519/) | FINAL + recursive allocatable ICE | 1eb696fc092 | [#4](https://github.com/krystophny/gcc-dev/issues/4) |
| [92613](92613/) | -cpp -fpreprocessed warning | 15ffee4e129 | [#7](https://github.com/krystophny/gcc-dev/issues/7) |
| [96255](96255/) | DO CONCURRENT type-spec | 5e62a23cc3a | [#1](https://github.com/krystophny/gcc-dev/issues/1) |
| [107721](107721/) | Array constructor type-spec | c50d263beff | [#6](https://github.com/krystophny/gcc-dev/issues/6) |
| [121472](121472/) | Constructor/finalizer ICE | 5bb465a7896 | [#2](https://github.com/krystophny/gcc-dev/issues/2) |
| [121475](121475/) | Function result finalization | a30b5f23b58 | [#8](https://github.com/krystophny/gcc-dev/issues/8) |
| [121628](121628/) | Recursive allocatable deep copy | a1fe2cfa896 | [#5](https://github.com/krystophny/gcc-dev/issues/5) |

## Directory Structure

Each PR directory contains:

```
pr/<number>/
├── README.md           # Links, status, analysis
├── reproducer.f90      # Minimal test case
├── 0001-*.patch        # Exported patch (if applicable)
└── Makefile            # Optional multi-compiler testing
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

## Links

- [GCC Bugzilla](https://gcc.gnu.org/bugzilla/)
- [GitHub Issues](https://github.com/krystophny/gcc-dev/issues)
- [Development Guide](../CLAUDE.md)
