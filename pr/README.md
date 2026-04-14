# GCC PR Directories

This directory holds per-PR bug work for GCC Fortran and related runtime work.

## What lives in each PR directory

Each `pr/<number>/README.md` is intentionally slim:
- **Bugzilla:** the upstream bug being tracked
- **GitHub issue:** the local tracking issue, when one exists
- **Technical notes:** durable context such as reproducer shape, root cause, and fix strategy

Workflow state does **not** live in the per-PR README anymore.

Current state is published in:
- GitHub issues in `krystophny/gcc-dev`
- `pr/<number>/status.json`
- generated summaries such as `backport-matrix.md`

## Directory Structure

Each PR directory typically contains:

```text
pr/<number>/
├── README.md           # Bugzilla link, issue link, durable technical notes
├── status.json         # Canonical machine-readable workflow state
├── reproducer.f90      # Minimal test case
├── 0001-*.patch        # Exported patch (if applicable)
├── submission/         # Generated maintainer/Bugzilla/mail packets
├── backports/          # Branch-specific patch and status packets
└── Makefile            # Optional multi-compiler testing
```

## Workflow Commands

```bash
# Refresh metadata from README links, Bugzilla, and existing status.json state
python3 scripts/gcc-workflow.py sync-metadata --all

# Publish current state into linked GitHub issues with gh CLI
python3 scripts/gcc-workflow.py sync-issues --all

# Regenerate maintainer packets and backport summaries
python3 scripts/gcc-workflow.py render-packet --all --regressions
python3 scripts/gcc-workflow.py scan-regressions
```

## Links

- [GCC Bugzilla](https://gcc.gnu.org/bugzilla/)
- [GitHub Issues](https://github.com/krystophny/gcc-dev/issues)
- [Development Guide](../CLAUDE.md)
