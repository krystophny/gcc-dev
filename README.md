# GCC Fortran Development

Meta-repository for GCC Fortran frontend and libgomp development.

## Quick Start

```bash
# Build local dev compiler
cd gcc-build && make -j$(nproc)

# Test with GPU offload (requires /opt/gcc16)
/opt/gcc16/bin/gfortran -fopenacc -foffload=nvptx-none test.f90
LD_LIBRARY_PATH=/opt/gcc16/lib64 ./a.out
```

## Structure

| Directory | Purpose |
|-----------|---------|
| `gcc/` | GCC source (separate git repo) |
| `gcc-build/` | Local development build |
| `pr/` | Bug reproducers and patches |
| `scripts/` | Build scripts for /opt/gcc16 |

## Tracking Model

Per-PR `README.md` files now keep only durable context:
- Bugzilla link
- GitHub issue link (when one exists)
- technical notes such as root cause, reproducer shape, and fix strategy

Live workflow state lives in GitHub issues and structured metadata:
- GitHub issues: current merge / patch / review status
- `pr/<number>/status.json`: machine-readable local workflow state
- `pr/backport-matrix.{md,json}`: generated branch/backport overview

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete development guide
- [pr/README.md](pr/README.md) - PR tracking overview
- [pr/regression-status.md](pr/regression-status.md) - Current Fortran regression summary
- [pr/backport-matrix.md](pr/backport-matrix.md) - Regression backport status
- [docs/gcc-trunk-contributor-stats-2026.md](docs/gcc-trunk-contributor-stats-2026.md) - 2026 GCC-wide trunk contribution report
- [docs/bugzilla-stats/2026-04-14-summary.json](docs/bugzilla-stats/2026-04-14-summary.json) - 1-year GCC/Fortran bug and regression snapshot

## Provenance Audit

Use the meta-repo provenance checker to rank testsuite files that look copied,
adapted, or externally licensed without enough local attribution:

```bash
make provenance-check
python3 scripts/check_testsuite_provenance.py --top 100 --json /tmp/provenance.json
python3 scripts/check_testsuite_provenance.py --include-testsuites --scope local --top 100 --json /tmp/provenance-tests-local.json
python3 scripts/check_testsuite_provenance.py --include-testsuites --scope all --top 100 --json /tmp/provenance-tests-all.json
```

The checker excludes `gcc/gcc/testsuite` and `gcc/libgomp/testsuite` by
default for now. Pass `--include-testsuites` to opt in to scanning them. When
enabled, `--scope local` reports only tests that are locally added or modified
relative to `upstream/master` plus uncommitted local test changes, while
`--scope all` performs a whole-tree historical audit.

It scores external-origin clues, nearby license files, SPDX/GNU metadata, and
optional reviewed path rules from `.provenance/testsuites.toml`.

Manifest entries can mark reviewed files as:
- `false_positive`: reviewed and suppressed from the default report
- `accepted_external`: external content with an adequate attribution trail
- `project_policy`: inherited tests accepted by GCC testsuite policy and suppressed by default
- `needs_local_license`: real external content that still needs cleaner local attribution or license placement

## Backport Workflow

Structured PR metadata now lives in `pr/<number>/status.json`.
Generated maintainer packets live under `pr/<number>/submission/`, and
branch-specific backport state lives under `pr/<number>/backports/`.

```bash
# Seed or refresh structured metadata
python3 scripts/gcc-workflow.py sync-metadata --all

# Push current workflow state into linked GitHub issues
python3 scripts/gcc-workflow.py sync-issues --all

# Regenerate maintainer packets for regression PRs
python3 scripts/gcc-workflow.py render-packet --all --regressions

# Write the top-level regression/backport matrix
python3 scripts/gcc-workflow.py scan-regressions

# Prepare and run branch applicability checks
python3 scripts/gcc-workflow.py branch-check --branches gcc-15,gcc-14,gcc-13

# Dry-run upstream submission for a generated packet
python3 scripts/gcc-workflow.py submit-bugzilla 120723 --branch trunk
python3 scripts/gcc-workflow.py submit-mail 120723 --branch gcc-15
```

## Installed Compilers

| Path | Description |
|------|-------------|
| `/opt/gcc16` | GCC 16 with NVPTX offload (local patches) |
| `/opt/gcc16-master` | Upstream master (no patches) |

## Links

- [GCC Bugzilla](https://gcc.gnu.org/bugzilla/)
- [GitHub Issues](https://github.com/krystophny/gcc-dev/issues)
- [GCC Fortran Mailing List](https://gcc.gnu.org/mailman/listinfo/fortran)
