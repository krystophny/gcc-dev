# Sync Issues

Synchronize GitHub issues with upstream GCC master and Bugzilla status.

## Full Sync

Run the complete sync workflow:

```bash
scripts/sync-issues.sh full
```

This runs: fetch, check-merged, close-merged, regressions, bugzilla-status.

After running, interpret the output and:

1. **Update CLAUDE.md** - Move newly merged PRs from the "Current Patch Status"
   table to the "Merged upstream" list (comma-separated, sorted numerically).
2. **Report untracked regressions** - List any Bugzilla regressions not yet
   tracked as GitHub issues. If the user asks, create issues for them using:
   ```bash
   gh issue create --title "PR<number>: <summary>" --body "<bugzilla link>"
   ```
3. **Report Bugzilla status changes** - Flag any issues where Bugzilla shows
   RESOLVED/FIXED but the GitHub issue is still open.

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

## CLAUDE.md Update Rules

When updating the "Merged upstream" list in CLAUDE.md:

- The list is a single comma-separated line of PR numbers, sorted numerically.
- Remove the corresponding row from the "Current Patch Status" table.
- Use `git -C gcc gcc-descr <hash>` to get the GCC revision tag for the
  close comment if not already provided by the script output.

## Important

- The script uses `scripts/gcc-bugzilla.sh` for Bugzilla queries (read-only).
- The script uses `gh` for GitHub operations.
- The GCC source repo is in `gcc/` with remote `upstream` pointing to gcc.gnu.org.
- Always run from the repo root (`/home/ert/code/gcc-dev`).
- The `close-merged` subcommand requires confirmation unless `--yes` is passed.
