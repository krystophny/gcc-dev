# Upstream Submission

## GCC upstream AI policy (2026), read first

Canonical text: https://gcc.gnu.org/ai-policy.html (CC0; announced
2026-07-28 by the steering committee, authored via the AI policy working
group led by Jonathan Wakely; review promised by start of 2027).
Summary of its operative rules:

- GCC **declines legally significant contributions** (GNU threshold:
  "around 15 lines of code and/or text") **which include LLM-generated
  content or are derived from LLM-generated content**. "Derived from"
  is not further defined.
- **Legally insignificant LLM-generated contributions are acceptable**
  if they meet the usual prerequisites and are **clearly marked**.
- **Test cases generated in whole or in part by an LLM are acceptable
  at any size** (explicit exception), at maintainer discretion.
- Any contribution of LLM-generated content **must carry an
  `Assisted-by:` tag**; a human must sign off (DCO), understand the
  change, and be able to answer questions.
- LLM use for research, analysis, bug discovery and reporting, patch
  review, and debugging is fine as long as the output is not included
  in the contribution; "output should not be sent verbatim without due
  consideration".

Consequences for this workflow, whose fixes are LLM-derived:

- **Legally significant code patches (≈15+ changed lines) are never
  offered to upstream GCC**: no patch attachments on Bugzilla, no
  gcc-patches@ submissions. They land on `lazy-fortran/gcc` instead.
- **Small fixes below the legal-significance threshold and testcases of
  any size MAY be offered upstream**, with an `Assisted-by:` tag naming
  the model, the user's Signed-off-by, and explicit user permission per
  submission. When in doubt whether a fix is "legally significant",
  keep it fork-only.
- **Bug reports, root-cause analysis, and reduced reproducers on
  Bugzilla remain welcome** and are the main way this work helps
  upstream. Write them deliberately, never paste raw model output, and
  disclose AI involvement honestly.
- Never present LLM-derived work upstream as if it were unassisted
  human work; that, not the fork, is what would actually damage GCC.

**ABSOLUTELY FORBIDDEN without explicit user permission:**
- `git send-email` to gcc-patches@gcc.gnu.org
- Posting to any GCC mailing list
- Creating or modifying GCC Bugzilla bugs/comments/attachments without explicit
  user permission and manual confirmation

**Single standing exception (user authorization 2026-07-29, revised
2026-07-30):** `scripts/bugzilla-pr-notify.sh` may post a short
comment linking a lazy-fortran/gcc PR. Lead: "Open for review, comments welcome: <URL>"
(merged PRs: "Fixed in the Lazy Fortran GCC fork: <URL>"). Then the
content: what the patch changes, what was tested,
and how it relates to prior patches and discussion on the bug. No AI
disclaimer, no boilerplate, no filler phrases. Write like a GCC
contributor: plain sentences, concrete facts.
Max ~15 lines. Write the body to a file, check the dry run, then
`--execute`. Anything else is an ordinary Bugzilla write and needs
explicit permission.

**Brevity rule for everything public-facing:** Bugzilla comments and PR
descriptions must be short and targeted: a handful of lines a
maintainer can read in ten seconds. State the fact, the link, the
disclosure; no narrative, no process detail, no restating what the bug
tracker already says.

**NEVER use git send-email or gcc-send-patch.sh without the user explicitly
requesting it - this is a HARD RULE.** (With the AI policy above, these
tools are effectively legacy: even with permission, only non-code
content (reports, analysis, disclosed testcases) is eligible.)

Permitted without approval:
- Prepare patches, run tests, document readiness
- Push fix branches to origin (lazy-fortran/gcc fork)
- Create PRs in the fork
- Export patches with `git format-patch`
- All Bugzilla operations: `info`, `comments`, `attachments`, `download`,
  `search`, `regressions`

## Backport-aware workflow

```bash
# Refresh canonical per-PR metadata from tracked READMEs/patches
python3 scripts/gcc-workflow.py sync-metadata --all

# Render maintainer packets and the regression backport matrix
python3 scripts/gcc-workflow.py render-packet --all --regressions
python3 scripts/gcc-workflow.py scan-regressions

# Run release-branch applicability checks in dedicated worktrees/build dirs
python3 scripts/gcc-workflow.py branch-check --branches gcc-15,gcc-14,gcc-13

# Generated files:
#   pr/<n>/status.json
#   pr/<n>/submission/{maintainer-summary.md,bugzilla-comment.txt,mailing-list-cover.txt}
#   pr/<n>/backports/<branch>/
#   pr/backport-matrix.{md,json}
```

## Bugzilla CLI (`python-bugzilla`)

```bash
# --- Read-only (always permitted) ---

# Query bug info
scripts/gcc-bugzilla.sh info <pr-number>

# Show all comments on a bug
scripts/gcc-bugzilla.sh comments <pr-number>

# List all attachments on a bug
scripts/gcc-bugzilla.sh attachments <pr-number>

# Download all non-obsolete patch attachments
scripts/gcc-bugzilla.sh download <pr-number>              # default: pr/<n>/upstream-patches/
scripts/gcc-bugzilla.sh download <pr-number> /tmp/patches  # custom output dir

# Search open fortran bugs by summary text
scripts/gcc-bugzilla.sh search "ICE in fold_convert"

# List all open fortran regressions
scripts/gcc-bugzilla.sh regressions

# Login (one-time, saves token in ~/.bugzillarc)
scripts/gcc-bugzilla.sh login

# Generate one-year daily bug/resolution stats and plots for:
# - all GCC bugs
# - all GCC regressions
# - all Fortran bugs
# - all Fortran regressions
python3 scripts/gcc-bugzilla-stats.py --start 2025-04-14

# Saved snapshots live in:
#   docs/bugzilla-stats/DATE-summary.json
#   docs/bugzilla-stats/DATE-*.png

# --- Write operations (REQUIRE explicit user permission and manual confirmation) ---

# Post a plain comment
scripts/gcc-bugzilla.sh comment <pr-number> "<text>"
scripts/gcc-bugzilla.sh comment-file <pr-number> <file>

# Quote-reply to a specific comment (Bugzilla "> " quoting style)
scripts/gcc-bugzilla.sh reply <pr-number> <comment-number> "<text>"
scripts/gcc-bugzilla.sh reply-file <pr-number> <comment-number> <file>

# Attach a patch (optionally obsolete previous attachments)
scripts/gcc-bugzilla.sh attach <pr-number> <file> [description] [comment]
scripts/gcc-bugzilla.sh attach --comment-file <file> <pr-number> <file> [description]
scripts/gcc-bugzilla.sh attach --obsolete <att-id> <pr-number> <file> [description]

# Add CC entries to a bug
scripts/gcc-bugzilla.sh ensure-cc <pr-number> [email[,email...]]

# Submit the generated workflow packet
scripts/gcc-bugzilla.sh submit <pr-number> [--branch trunk|gcc-15|gcc-14|gcc-13] [--execute]
```

The stats script is intentionally light on Bugzilla:
- it uses the documented REST search endpoint `GET /bugzilla/rest.cgi/bug`
  for the current open set, the created-in-range set, and the closed/changed-in-range set
- it uses the documented bug history endpoint
  `GET /bugzilla/rest.cgi/bug/<id>/history?new_since=YYYY-MM-DD`
  only for bugs closed/changed in the requested window, caching responses under
  `~/.cache/gcc-dev-bugzilla-stats/`
- it derives exact first-resolution dates locally from history instead of issuing
  hundreds of per-day count queries

Write operations must be prepared in files first and then posted from those
reviewed files. `scripts/gcc-bugzilla.sh new` already takes a draft file, and
`comment-file`, `reply-file`, and `attach --comment-file` provide the same
file-first flow for other Bugzilla writes.

LLM-derived patches must use `gcc-workflow.py submit-bugzilla`. Before the
dry run or upload, it requires a one-commit format-patch with `Assisted-by:`
and `Signed-off-by:` tags. It counts additions and deletions outside paths
containing a `testsuite` component and blocks the submission at 15 changed
non-test lines. Test cases are counted separately and do not affect
eligibility. Ambiguous and binary diffs are blocked.

```bash
python3 scripts/gcc-workflow.py ai-eligibility \
  pr/<number>/0001-*.patch --expected-assistant 'GPT-5.6-sol (OpenAI)'
scripts/gcc-bugzilla.sh submit <number> \
  --expected-assistant 'GPT-5.6-sol (OpenAI)'       # dry run
GCC_BUGZILLA_MANUAL_CONFIRM=1 scripts/gcc-bugzilla.sh submit <number> \
  --expected-assistant 'GPT-5.6-sol (OpenAI)' --execute
```

Use `--obsolete <attachment-id>` on `submit` when an attributed patch
replaces an earlier attachment. A successful upload records
`submission_status.on_bugzilla` through `sync-metadata`. If an upload
succeeded before that local update, recover it with
`sync-metadata <number> --mark-on-bugzilla` after verifying the attachment.

Write operations are blocked unless `GCC_BUGZILLA_MANUAL_CONFIRM=1` is set
after manual review and explicit user confirmation. They still default to an
interactive `[y/N]` prompt. Use `GCC_BUGZILLA_ASSUME_YES=y` only after that
manual confirmation step; it must never be used to automate unreviewed posting.

When replying to Bugzilla comments, always use `reply` instead of `comment`
to produce proper quote-reply formatting.  This matches the convention used
by other GCC contributors (e.g., Mikael Morin) and keeps the thread readable.

## Mailing list (`git send-email`, configured in gcc/)

```bash
# Send patch (REQUIRES explicit user permission)
scripts/gcc-send-patch.sh pr/<number>/0001-*.patch

# Dry run (preview without sending, always permitted)
scripts/gcc-send-patch.sh --dry-run pr/<number>/0001-*.patch

# Send the generated packet (REQUIRES explicit user permission)
scripts/gcc-send-patch.sh submit <pr-number> [--branch trunk|gcc-15|gcc-14|gcc-13] [--execute]
```

Both scripts have interactive confirmation prompts as a safety net.
