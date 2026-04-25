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
`fortran@gcc.gnu.org`, `libstdc++@gcc.gnu.org`) want bottom-posted plain
text: the **quoted thread comes first (top), the reply text goes
underneath (below)**. Never top-post (reply on top, quote below) and
never reply with only a trimmed snippet of the immediate parent — the
**whole ancestor chain** must be visible above the new reply.

Drafting procedure:

1. Use `mcp__sloppy__mail_reply` with `quote_style: "bottom_post"` for
   the threading headers and the immediate-parent quote, **only when the
   parent already preserves the full ancestor chain in its body**.
   `mail_reply` does not walk the chain; it just quotes whichever body
   the parent kept.
2. When the parent has trimmed earlier ancestors (almost always the case
   on long GCC threads), fall back to `mcp__sloppy__mail_send` with
   `draft_only: true` and **hand-roll** the body:
   - Reconstruct the linear `In-Reply-To` chain from leaf back to the
     thread root by matching attribution lines (`On <date>, X wrote:`,
     `Am <de-date> schrieb X:`) and first-quoted paragraphs across
     `mail_message_get` bodies. EWS hides `In-Reply-To` headers so the
     match-by-content walk is the only option.
     A general-purpose subagent is well-suited to this.
   - Emit each ancestor's full body with one extra `>` per nesting
     level, plus an English `On <date>, <author> wrote:` attribution
     line at the matching depth.
   - Order top-down: quoted leaf first (depth 1), then progressively
     older ancestors at depths 2, 3, …; the reply text is the only
     unquoted block and sits at the very bottom.
   - Set `in_reply_to` to the leaf message-id and pass a full
     `references` chain root → leaf so the new reply lands at the tail
     of the existing thread and does not branch it.
3. Either way: plain text only, UTF-8, no HTML, no signatures past `-- \n`,
   and keep `gcc@gcc.gnu.org` plus the original Cc set in `cc`. If
   `reply_all: true` errors with `invalid address "X <X>"` (EWS's
   duplicated `Name <addr>` form), supply `to`/`cc` explicitly and set
   `reply_all: false`.

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
