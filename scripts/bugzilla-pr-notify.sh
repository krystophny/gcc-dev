#!/bin/bash
# bugzilla-pr-notify.sh - Post a short, substantive Bugzilla comment linking
# a lazy-fortran/gcc PR (open-for-review or merged).
#
# Standing user authorization (2026-07-29, revised 2026-07-30, see
# docs/upstream-submission.md): the comment must be a real description of
# what the PR's patch IS — what it changes, what was verified, and how it
# relates to existing patches and discussion on the bug. No boilerplate,
# no AI disclaimer. Any Bugzilla write outside this shape still requires
# explicit per-message user permission.
#
# Usage:
#   bugzilla-pr-notify.sh <bugzilla-pr> <github-pr-url> <body-file>            dry run
#   bugzilla-pr-notify.sh <bugzilla-pr> <github-pr-url> <body-file> --execute  post

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

[[ $# -ge 3 ]] || { echo "usage: $0 <bugzilla-pr> <github-pr-url> <body-file> [--execute]" >&2; exit 1; }
PR="$1"
URL="$2"
BODY="$3"
EXECUTE="${4:-}"

[[ "$PR" =~ ^[0-9]+$ ]] || { echo "ERROR: bugzilla PR must be numeric" >&2; exit 1; }
[[ "$URL" =~ ^https://github\.com/lazy-fortran/gcc/pull/[0-9]+$ ]] \
    || { echo "ERROR: URL must be a lazy-fortran/gcc pull request" >&2; exit 1; }
[[ -s "$BODY" ]] || { echo "ERROR: body file missing or empty" >&2; exit 1; }

grep -qF "$URL" "$BODY" \
    || { echo "ERROR: body must contain the PR URL $URL" >&2; exit 1; }
LINES=$(wc -l < "$BODY")
(( LINES <= 15 )) \
    || { echo "ERROR: body too long ($LINES lines, max 15) — keep it short and targeted" >&2; exit 1; }
grep -qiE 'ai-assisted|ai-policy|not submitted for inclusion|disclaimer' "$BODY" \
    && { echo "ERROR: drop the AI-disclaimer boilerplate; describe the fix instead" >&2; exit 1; }

echo "--- comment for PR $PR ---"
cat "$BODY"
echo "---------------------------"

if [[ "$EXECUTE" == "--execute" ]]; then
    GCC_BUGZILLA_MANUAL_CONFIRM=1 GCC_BUGZILLA_ASSUME_YES=y \
        "$SCRIPT_DIR/gcc-bugzilla.sh" comment-file "$PR" "$BODY"
else
    echo "(dry run; pass --execute to post)"
fi
