#!/bin/bash
# migrate-issues.sh - Move GitHub issues from the meta-repo to the fork.
#
# Copies each issue (title, body, labels) from krystophny/gcc-dev to
# lazy-fortran/gcc, cross-links both sides, and closes the source issue.
#
# Usage:
#   migrate-issues.sh                 Dry run over all open source issues
#   migrate-issues.sh --execute       Migrate all open source issues
#   migrate-issues.sh --execute 12 34 Migrate specific source issue numbers
#
# Env overrides: SRC_REPO (krystophny/gcc-dev), DST_REPO (lazy-fortran/gcc)

set -euo pipefail

SRC_REPO="${SRC_REPO:-krystophny/gcc-dev}"
DST_REPO="${DST_REPO:-lazy-fortran/gcc}"
EXECUTE=0
ISSUES=()

for arg in "$@"; do
    case "$arg" in
        --execute) EXECUTE=1 ;;
        --dry-run) EXECUTE=0 ;;
        [0-9]*) ISSUES+=("$arg") ;;
        *) echo "ERROR: unknown argument: $arg" >&2; exit 1 ;;
    esac
done

if [[ ${#ISSUES[@]} -eq 0 ]]; then
    mapfile -t ISSUES < <(gh issue list --repo "$SRC_REPO" --state open \
        --limit 500 --json number --jq '.[].number' | sort -n)
fi

echo "Source: $SRC_REPO  ->  Target: $DST_REPO"
echo "Issues to migrate: ${#ISSUES[@]}"
[[ $EXECUTE -eq 1 ]] || echo "(dry run; pass --execute to act)"

ensure_label() {
    local label="$1"
    gh label create "$label" --repo "$DST_REPO" --force >/dev/null 2>&1 || true
}

for num in "${ISSUES[@]}"; do
    json=$(gh issue view "$num" --repo "$SRC_REPO" \
        --json title,body,labels,url,state)
    title=$(jq -r '.title' <<<"$json")
    state=$(jq -r '.state' <<<"$json")
    url=$(jq -r '.url' <<<"$json")
    labels=$(jq -r '[.labels[].name] | join(",")' <<<"$json")

    if [[ "$state" != "OPEN" && ${#ISSUES[@]} -gt 1 ]]; then
        echo "skip #$num ($state): $title"
        continue
    fi
    echo "migrate #$num [$labels]: $title"
    [[ $EXECUTE -eq 1 ]] || continue

    body_file=$(mktemp)
    {
        echo "_Migrated from $url._"
        echo
        jq -r '.body' <<<"$json"
    } > "$body_file"

    if [[ -n "$labels" ]]; then
        IFS=',' read -ra label_arr <<<"$labels"
        for l in "${label_arr[@]}"; do ensure_label "$l"; done
    fi

    create_args=(--repo "$DST_REPO" --title "$title" --body-file "$body_file")
    [[ -n "$labels" ]] && create_args+=(--label "$labels")
    new_url=$(gh issue create "${create_args[@]}")
    rm -f "$body_file"
    echo "  -> $new_url"

    gh issue close "$num" --repo "$SRC_REPO" \
        --comment "Migrated to $new_url as part of the move to the $DST_REPO downstream fork."
done
