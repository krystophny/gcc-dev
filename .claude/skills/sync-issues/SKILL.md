# Sync Issues

Synchronize GitHub issues with upstream GCC master and Bugzilla status.

## Full Sync

Run the complete sync workflow:

```bash
scripts/sync-issues.sh full
```

This runs: fetch, check-merged, close-merged, regressions, bugzilla-status.

After running, interpret the output and:

1. **Report untracked regressions** - List any Bugzilla regressions not yet
   tracked as GitHub issues. If the user asks, create issues for them using:
   ```bash
   gh issue create --title "PR<number>: <summary>" --body "<bugzilla link>"
   ```
2. **Report Bugzilla status changes** - Flag any issues where Bugzilla shows
   RESOLVED/FIXED but the GitHub issue is still open.

Per-PR state lives in `pr/<number>/status.json` and is owned by
`scripts/gcc-workflow.py sync-metadata`. Do not hand-edit status fields in
markdown.

## Composable Sub-tasks

The user may request individual steps:

- **"check which PRs are merged"** - Run `scripts/sync-issues.sh check-merged`
- **"check if PR 12345 is merged"** - Run `scripts/sync-issues.sh check-merged --pr 12345`
- **"fetch upstream"** - Run `scripts/sync-issues.sh fetch`
- **"show bugzilla status"** - Run `scripts/sync-issues.sh bugzilla-status`
- **"bugzilla status for PR 12345"** - Run `scripts/sync-issues.sh bugzilla-status --pr 12345`
- **"find untracked regressions"** - Run `scripts/sync-issues.sh regressions`
- **"close merged issues"** - Run `scripts/sync-issues.sh close-merged` (requires confirmation or `--yes`)
- **"dry run close"** - Run `scripts/sync-issues.sh close-merged --dry-run`

## Important

- The script uses `scripts/gcc-bugzilla.sh` for Bugzilla queries (read-only).
- The script uses `gh` for GitHub operations.
- The GCC source repo is in `gcc/` with remote `upstream` pointing to gcc.gnu.org.
- Always run from the repo root (`/home/ert/code/gcc-dev`).
- The `close-merged` subcommand requires confirmation unless `--yes` is passed.
