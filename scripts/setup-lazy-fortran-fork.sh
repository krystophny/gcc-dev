#!/bin/bash
# setup-lazy-fortran-fork.sh - One-shot GitHub-side bootstrap of the
# lazy-fortran/gcc downstream fork.
#
#   1. Fork gcc-mirror/gcc (1:1 mirror of gcc.gnu.org) into the
#      lazy-fortran org as lazy-fortran/gcc (server-side, no push needed).
#   2. Create the `main` branch from `master` (main = GCC master + fixes).
#   3. Enable issues on the fork (GitHub disables them on forks).
#   4. Migrate all open issues from krystophny/gcc-dev (migrate-issues.sh).
#   5. Archive the retired krystophny/gcc mirror (reversible; delete is a
#      manual decision afterwards).
#
# Also prints the remote rewiring to run in the local gcc/ checkout.
#
# Usage: setup-lazy-fortran-fork.sh [--skip-archive] [--skip-issues]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ORG="lazy-fortran"
FORK="$ORG/gcc"
OLD_MIRROR="krystophny/gcc"
SKIP_ARCHIVE=0
SKIP_ISSUES=0

for arg in "$@"; do
    case "$arg" in
        --skip-archive) SKIP_ARCHIVE=1 ;;
        --skip-issues) SKIP_ISSUES=1 ;;
        *) echo "ERROR: unknown argument: $arg" >&2; exit 1 ;;
    esac
done

echo "== 1/5 fork gcc-mirror/gcc -> $FORK"
if gh repo view "$FORK" --json name >/dev/null 2>&1; then
    echo "   already exists, skipping"
else
    gh repo fork gcc-mirror/gcc --org "$ORG" --fork-name gcc --clone=false
fi

echo "== 2/5 create main branch from master"
if ! gh api "/repos/$FORK/branches/main" --jq .name >/dev/null 2>&1; then
    sha=$(gh api "/repos/$FORK/branches/master" --jq '.commit.sha')
    gh api -X POST "/repos/$FORK/git/refs" \
        -f ref="refs/heads/main" -f sha="$sha" >/dev/null
    echo "   main created at $sha"
else
    echo "   main already exists, skipping"
fi
gh repo edit "$FORK" --default-branch main

echo "== 3/5 enable issues + squash-merge-only PRs"
gh repo edit "$FORK" --enable-issues \
    --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false \
    --description "Downstream GCC distribution by the Lazy Fortran project: GNU Fortran correctness, OpenMP, OpenACC. One squash-merged PR per upstream Bugzilla PR."

if [[ $SKIP_ISSUES -eq 0 ]]; then
    echo "== 4/5 migrate issues from krystophny/gcc-dev"
    "$SCRIPT_DIR/migrate-issues.sh" --execute
else
    echo "== 4/5 issue migration skipped"
fi

if [[ $SKIP_ARCHIVE -eq 0 ]]; then
    echo "== 5/5 archive retired mirror $OLD_MIRROR"
    gh repo archive "$OLD_MIRROR" --yes || echo "   archive failed (already archived?)"
else
    echo "== 5/5 archive skipped"
fi

cat <<'EOF'

Done. Rewire the local gcc/ checkout on the build machine:

  git -C gcc remote remove origin 2>/dev/null || true
  git -C gcc remote add origin git@github.com:lazy-fortran/gcc.git
  git -C gcc fetch origin
  # upstream stays gcc.gnu.org/git/gcc.git (never push)

Deleting krystophny/gcc (instead of archive) is a manual decision:
  gh repo delete krystophny/gcc   # needs delete_repo scope
EOF
