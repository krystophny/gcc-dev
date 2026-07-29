# GCC Fortran Development

Meta-repository for my work on the GCC Fortran frontend, libgomp, and
libgfortran. Holds reproducers, exported `.patch` files, build scripts,
provenance tooling, and per-PR notes; the GCC source itself lives in
the embedded `gcc/` git repo (separate history).

> **Notice.** This is a personal research and development meta-repo; it
> is not affiliated with the GCC project or the FSF. Provenance notes,
> scanner output, severity tags, and chain-of-custody narratives are
> working observations, not legal conclusions or allegations against
> any contributor or project. See [`DISCLAIMER.md`](DISCLAIMER.md) for
> the no-warranty / non-liability terms and [`LICENSE`](LICENSE) for
> the GPL-3.0-or-later license.

## Layout

| Path | Contents |
|------|----------|
| `gcc/` | GCC source (separate repo, downstream fork at [lazy-fortran/gcc](https://github.com/lazy-fortran/gcc)) |
| `gcc-build/` | Local development build (untracked) |
| `pr/<number>/` | Reproducer, exported patch(es), README, machine-readable `status.json` |
| `scripts/` | Build helpers, workflow automation, provenance scanners |
| `docs/` | Workflow, build, bug-pattern and contribution documentation |

## Quick start

```bash
# rebuild after edits
cd gcc-build/gcc && make -j$(nproc)

# run the Fortran frontend testsuite
make -j$(nproc) -k check-gfortran > /tmp/test.log 2>&1
grep -cE "^FAIL|^XPASS" testsuite/gfortran/gfortran.sum   # must be 0 new

# run the libgomp Fortran runtime tests
cd .. && make -j$(nproc) check-target-libgomp-fortran \
    > /tmp/libgomp-fortran.log 2>&1
```

Single test: `make check-gfortran RUNTESTFLAGS="dg.exp=pr<N>.f90"`.

## Documentation

- [docs/build-and-test.md](docs/build-and-test.md) — compilers, build configs,
  check-gfortran, OpenACC offload, aarch64 VMs
- [docs/patch-workflow.md](docs/patch-workflow.md) — triage, commit rules,
  provenance, PR layout, GitHub issue labelling
- [docs/upstream-submission.md](docs/upstream-submission.md) — Bugzilla CLI,
  mailing-list submission, backport-aware workflow
- [docs/bug-patterns.md](docs/bug-patterns.md) — catalogue of recurring
  root-cause patterns with symptom / cause / fix / evidence
- [docs/provenance-research.md](docs/provenance-research.md) — how to chase a
  provenance finding from scanner hit to upstream introduction commit
- [docs/upstream-master-commits.md](docs/upstream-master-commits.md) —
  list of my commits currently on GCC `master`, with mirror links and
  AI-assistance attribution
- [CLAUDE.md](CLAUDE.md) — agent rules and project pointers

## PR tracking

State for each open PR lives next to it:

- `pr/<number>/README.md` — durable context: Bugzilla / GitHub-issue link,
  reproducer shape, root cause, fix strategy
- `pr/<number>/status.json` — machine-readable workflow state, schema
  in `pr/schema.json`, written by `gcc-workflow.py sync-metadata`
- `pr/backport-matrix.{md,json}` — generated branch / backport overview
- GitHub issues — current merge / patch / review status

Backport, packet rendering and submission helpers all run through
`python3 scripts/gcc-workflow.py ...`; see
[docs/upstream-submission.md](docs/upstream-submission.md).

`make check-meta` validates the schema, scans for orphan status docs,
and warns on stale snapshot dates. `make install-hooks` installs the
pre-push hook that runs the same checks plus a secret/scrape scan.

## Provenance audit

Rank testsuite files that look copied, adapted, or externally licensed
without enough local attribution:

```bash
make provenance-check
python3 scripts/check_testsuite_provenance.py --top 100 \
    --json /tmp/provenance.json
python3 scripts/check_testsuite_provenance.py \
    --include-testsuites --scope all --top 100 \
    --json /tmp/provenance-tests-all.json
```

Manifest entries in `.provenance/testsuites.toml` mark reviewed files as
`false_positive`, `accepted_external`, `project_policy`, or
`needs_local_license`.

## Links

- [GCC Bugzilla](https://gcc.gnu.org/bugzilla/)
- [GCC Fortran mailing list](https://gcc.gnu.org/mailman/listinfo/fortran)
- [lazy-fortran/gcc fork and issues](https://github.com/lazy-fortran/gcc)
