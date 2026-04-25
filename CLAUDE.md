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

## Meta-repo external-content policy

This meta-repo is GPL-3.0-or-later (`LICENSE`). Track only:

- The user's own work (patches, reproducers, notes, scripts, docs).
- Download/fetch scripts and TOML configs that point at canonical upstream
  sources (e.g. `scripts/provenance/fetch_corpus.sh`,
  `.provenance/corpus-sources.toml`). External code itself is fetched into
  gitignored `corpusbin/`, `gcc/`, `third_party/` and never committed.

Forbidden in tracked content:

- Verbatim Bugzilla page scrapes (`bugzilla.txt` HTML/text dumps). The GCC
  Bugzilla and mailing-list archives carry no explicit license grant for
  user-submitted content (see gcc.gnu.org/contribute, /bugs, /lists);
  redistribution outside GCC is legally ambiguous, and a logged-in scrape
  also leaks the user's own email in the page header. Link to the
  Bugzilla URL instead.
- Direct Bugzilla attachments stored under their attachment-id name
  (`attachment-NNNNN-*.f90`). Same reason. Either rewrite as a local
  reduction (the user's own work, GPL) or link to the Bugzilla URL.
- Mailing-list message bodies copied wholesale. Quote only the minimum
  needed for context; otherwise link to the pipermail/inbox URL.

Allowed external content:

- Files derived from a permissively-licensed upstream that explicitly
  permits redistribution (Apache-2.0, BSD, MIT, Boost, Fujitsu CTS's
  Apache-2.0 WITH LLVM-exception). These must carry an in-file provenance
  header naming the exact upstream file, project URL, license, and the
  intermediary (e.g. Bugzilla reporter who reduced it). Pattern:

  ```
  ! Reduced from github.com/fujitsu/compiler-test-suite Fortran/0413/0413_0003.f90
  ! by David Binderman <dcb314@hotmail.com> via PR fortran/123949 Comment #0.
  ! Fujitsu CTS is Apache-2.0 WITH LLVM-exception (GPL-3-compatible).
  ```

When in doubt, drop the file and keep only the user's own reduction.

### Pre-push checklist (mandatory before every push to `origin`)

This repo is public on GitHub. Treat every push as final publication.
Before `git push` (or `git push --force`), explicitly walk this list and
report what was checked — no shortcuts:

1. `git diff --stat origin/main...HEAD` — review every path being added
   or modified. For each file, confirm it is the user's own work, an
   allowed permissively-licensed derivative with proper provenance
   header, or a link/script to external content.
2. `git diff origin/main...HEAD -- '*.txt' '*.md' '*.f90' '*.f' '*.for'
   '*.c' '*.cc' '*.h' '*.patch'` — scan diffs for verbatim Bugzilla
   page scrapes (`Log out <email>`, `[reply] [-]Comment N`,
   `attachment-NNNNN`), verbatim mailing-list bodies, raw Bugzilla
   attachment filenames, or external testcases without a provenance
   header.
3. `git ls-files | xargs grep -lE 'attachment-[0-9]+' && git ls-files |
   xargs grep -l 'Log out '` — must return empty.
4. Secret scan: `git diff origin/main...HEAD | grep -iE
   '(api[_-]?key|api[_-]?token|secret[_-]?key|password|BEGIN (RSA|
   OPENSSH|PGP|EC) PRIVATE|ghp_|glpat-|sk-)'` — must be empty.
5. Personal-data scan: search the diff for non-user emails and decide
   per-occurrence whether the email is already public via GCC
   convention (`Contributed by <reporter>` lines, Signed-off-by
   trailers, ChangeLog Co-authored-by) or a leak.
6. If anything fails: stop, fix in a new commit (or amend if the
   problem commit is local-only), re-run the checklist, then push.
7. Force-push (`--force-with-lease`): in addition to 1-6, confirm the
   history rewrite scope with the user before pushing. Do not force-
   push without explicit user authorization for that specific push.

Apply the same checklist to the embedded `gcc/` worktree before any
fork push to `github.com/krystophny/gcc`.

## Patch status — sources of truth

Per-PR state lives next to each patch; do not duplicate it here.

- `pr/<number>/status.json` — machine-readable: `fix_status`,
  `bugzilla.{status,resolution}`, `trunk.commit`, backports.
- `pr/<number>/README.md` — human summary.
- `pr/backport-matrix.{md,json}` — generated backport overview.
- `docs/upstream-master-commits.md` — commits on GCC trunk authored by
  the user, with mirror links and AI-assistance attribution.
- Upstream `gcc/` worktree (`upstream/master`) — authoritative for
  whether a patch landed; query with `git -C gcc log upstream/master
  --grep PR<N>`.
