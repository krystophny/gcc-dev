#!/bin/bash
# bugzilla-pr-notify.sh - Post a short Bugzilla comment linking a finished
# (squash-merged) lazy-fortran/gcc PR.
#
# This exact template carries standing user authorization (2026-07-29, see
# docs/upstream-submission.md). Any other Bugzilla write still requires
# explicit per-message user permission.
#
# Usage:
#   bugzilla-pr-notify.sh <bugzilla-pr> <github-pr-url>            dry run
#   bugzilla-pr-notify.sh <bugzilla-pr> <github-pr-url> --execute  post

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

[[ $# -ge 2 ]] || { echo "usage: $0 <bugzilla-pr> <github-pr-url> [--execute]" >&2; exit 1; }
PR="$1"
URL="$2"
EXECUTE="${3:-}"

[[ "$PR" =~ ^[0-9]+$ ]] || { echo "ERROR: bugzilla PR must be numeric" >&2; exit 1; }
[[ "$URL" =~ ^https://github\.com/lazy-fortran/gcc/pull/[0-9]+$ ]] \
    || { echo "ERROR: URL must be a lazy-fortran/gcc pull request" >&2; exit 1; }

COMMENT_FILE="$(mktemp)"
trap 'rm -f "$COMMENT_FILE"' EXIT
cat > "$COMMENT_FILE" <<EOF
This is fixed in the Lazy Fortran GCC fork: $URL
(single squashed commit, testcase, and review log). AI-assisted work,
linked for reference only — not submitted for inclusion, per
https://gcc.gnu.org/ai-policy.html.
EOF

echo "--- comment for PR $PR ---"
cat "$COMMENT_FILE"
echo "---------------------------"

if [[ "$EXECUTE" == "--execute" ]]; then
    GCC_BUGZILLA_MANUAL_CONFIRM=1 GCC_BUGZILLA_ASSUME_YES=y \
        "$SCRIPT_DIR/gcc-bugzilla.sh" comment-file "$PR" "$COMMENT_FILE"
else
    echo "(dry run; pass --execute to post)"
fi
