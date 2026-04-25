# GCC Fortran Development Meta-Repository

Details live in `docs/`:
- `docs/build-and-test.md` — compilers, build configs, check-gfortran, OpenACC,
  debugging, aarch64 VMs, key files by domain
- `docs/patch-workflow.md` — triage, commit rules, provenance, PR layout,
  GitHub issue labeling, fix-development do/don't lists
- `docs/upstream-submission.md` — Bugzilla CLI, mailing-list submission,
  backport-aware workflow
- `docs/bug-patterns.md` — catalogue of 14 recurring root-cause patterns
  with symptom/cause/fix/evidence
- `docs/provenance-research.md` — how to research a provenance finding end
  to end: scanner hit -> GCC and upstream introduction commits -> mailing
  list -> chain of custody -> correct fix that matches the subtree convention

## Repository Structure

```
gcc-dev/                    # META-REPO (GitHub: krystophny/gcc-dev)
├── gcc/                    # GCC SOURCE (separate git repo, local branches only)
│   ├── gcc/fortran/        # Fortran frontend
│   ├── gcc/testsuite/gfortran.dg/  # Frontend tests
│   └── libgomp/            # OpenMP/OpenACC runtime library
├── gcc-build/              # Local dev build (not tracked)
├── pr/                     # Bug work directories (tracked)
│   └── <number>/           # reproducer.f90, *.patch, README.md
├── gcc-offload-build/      # NVPTX offload build + install (not tracked)
└── scripts/                # Build scripts for offload compiler
```

**Git remotes in gcc/:**
- `origin` = github.com/krystophny/gcc (fork, safe to push)
- `upstream` = gcc.gnu.org/git/gcc.git (NEVER push, use git send-email)

The fork carries only `origin/master` tracking upstream. All patch work is
stored as exported `.patch` files under `pr/<number>/` in this meta-repo;
there are no persistent `pr*-fix` branches on the fork. Create a local
branch off `upstream/master` for each fix, commit, export, and delete the
branch once the patch file is in `pr/<number>/`.

```bash
git -C gcc format-patch -1 HEAD -o ../pr/<number>/       # export patch
```

Prefer standard Git workflows plus the `git gcc-*` helpers (`git gcc-verify`,
`git gcc-commit-mklog`, `git gcc-mklog`, `git gcc-descr`, `git gcc-undescr`)
over ad-hoc bookkeeping.

## Quick Reference

Build trunk, rebuild after edits, and run the full validation suite:

```bash
cd gcc-build/gcc && make -j32                                   # rebuild
make -j32 -k check-gfortran > /tmp/test.log 2>&1                # frontend
grep -cE "^FAIL|^XPASS" testsuite/gfortran/gfortran.sum         # must be 0 new
cd .. && make -j32 check-target-libgomp-fortran \
  > /tmp/libgomp-fortran.log 2>&1                               # runtime
```

Single test: `make check-gfortran RUNTESTFLAGS="dg.exp=pr<N>.f90"`.

Both suites must pass with zero new FAIL/XPASS before posting any patch. See
`docs/build-and-test.md` for coverage details, OpenACC caveats, DejaGnu
conventions, and OpenMP testcase placement rules.

## Patch Submission Ground Rules

Never invoke `git send-email`, `scripts/gcc-send-patch.sh`, or any Bugzilla
write operation without explicit user permission. Fork pushes, patch export,
and all read-only Bugzilla queries are fine. See
`docs/upstream-submission.md` for the full list of tools and confirmation
requirements.

Every commit on a patch branch requires:
- `-s` (Signed-off-by)
- `Assisted-by:` trailer naming the model used
- `git gcc-verify HEAD` passing
- both trailers re-verified in the exported patch

Full procedure and the `GCC_FORCE_MKLOG=1` commit recipe are in
`docs/patch-workflow.md`.

## Mailing-list reply etiquette

GCC lists (`gcc@gcc.gnu.org`, `gcc-patches@gcc.gnu.org`,
`fortran@gcc.gnu.org`, `libstdc++@gcc.gnu.org`) are interleaved /
bottom-post: the quoted thread is shown top-down (oldest first) and the
new reply sits at the bottom. Always use the sloppy MCP `mail_reply`
tool with `quote_style: "bottom_post"` — it formats the quoted parent
and threading headers correctly out of the box. Do not hand-roll the
quote with `mail_send` unless `mail_reply` cannot reach the message.

Required behaviour for every drafted reply:

- `mcp__sloppy__mail_reply`, `quote_style: "bottom_post"`, `draft_only: true`.
- `message_id` = the **tail** of the discussion (the most recent message
  in the thread), so the new reply lands at the end and does not branch
  the thread.
- `reply_all: true` to keep the existing `Cc:` set intact, including
  `gcc@gcc.gnu.org` for thread continuity. If EWS rejects the
  reply-all merge with `invalid address "X <X>"` (duplicated `Name
  <addr>` form), fall back to `reply_all: false` plus explicit `to:` and
  `cc:` lists rebuilt by hand from the original recipients.
- Plain text only, UTF-8, no HTML, no signatures past `-- \n`.

Save mailing-list replies as drafts in the user's Exchange Drafts and
let the user review and send. Never send to a public list without
explicit user permission for that specific message.

## Provenance Ground Rules

Never copy anything verbatim into `gcc/` — not code, not tests, not
reproducers. Bugzilla reporters frequently paste third-party test-suite
content (Fujitsu CTS, NAG, commercial benchmarks) directly into comments;
public posting in a bug tracker is not a license grant. Before deriving
any testcase from a Bugzilla-posted reproducer, trace its origin and
rewrite from scratch with different variable names, shapes, format
strings, and surrounding structure. Only isolated factual bug-trigger
values (`INT_MAX`, kind boundaries, standards constants) are safe to
reuse. If you cannot rewrite cleanly, ship the code fix without a
testcase rather than a license-unclear one. Full rules in
`docs/patch-workflow.md` under "Provenance review".

## Current Patch Status

Active patches live as exported `.patch` files under `pr/<number>/` in this
meta-repo. See `pr/<number>/README.md` and `pr/<number>/status.json` for the
current state (on-bugzilla / on-mailing-list / merged), and
`pr/backport-matrix.md` for backport coverage.

| PR | Description |
|----|-------------|
| 79524 | Fix heap-use-after-free in resolve_charlen |
| 85352 | Fix bogus reject of ENTRY specification expressions |
| 93715 | Fix ICE in gfc_trans_auto_array_allocation for scalar coarray |
| 93814 | Fix ICE in build_entry_thunks with CHARACTER bind(c) ENTRY |
| 94978 | Fix bogus array-out-of-bounds warning in do-loop |
| 96986 | Fix false explicit-interface-required for ENTRY with volatile |
| 102430 | Reject array/allocatable LINEAR on DO |
| 103367 | Fix ICE in gfc_conv_array_initializer with invalid index |
| 109788 | Fix character SPREAD intrinsic descriptor specialization |
| 123280+96080 | Fix acc_is_present for assumed-shape and pointers |
| 103276 | Skip pointer mapping for pass-by-ref in ENTER/EXIT DATA |
| 123252 | Map scalar fields on enter data for components |
| 123282 | Fix OpenACC refcount for Fortran allocatable array descriptors |

**Merged upstream:** 32365, 82721, 90519, 92613, 95338, 96255, 100155, 100194,
102459, 102596, 103139, 106946, 107721, 108382, 110877, 120286, 120723,
121472, 121475, 121628, 123868, 123943, 123947, 123949, 124208, 124235,
124482, 124512, 124631, 124661, 124666, 124751
