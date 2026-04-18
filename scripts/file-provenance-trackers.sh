#!/bin/bash
# file-provenance-trackers.sh - Create local trackers for reviewed provenance findings
#
# Usage:
#   file-provenance-trackers.sh [--execute] [--bugzilla-id <id>] [slug...]
#
# Supported slugs:
#   go-test

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISSUE_REPO="krystophny/gcc-dev"
EXECUTE=0
BUGZILLA_ID=""

usage() {
    cat <<'EOF'
Usage: file-provenance-trackers.sh [--execute] [--bugzilla-id <id>] [slug...]

Create or reuse local GitHub tracker issues and pr/<bug>/README.md entries for
reviewed provenance findings.

This script never creates or modifies GCC Bugzilla bugs. Create or review the
Bugzilla draft manually first, then rerun this script with --bugzilla-id or
after the bug is discoverable by exact-summary search.

Options:
  --execute            Actually create missing GitHub issues and local files
  --bugzilla-id <id>   Use this Bugzilla bug id directly instead of searching

Supported slugs:
  go-test
EOF
}

find_existing_bug() {
    local component="$1"
    local summary="$2"

    bugzilla --bugzilla=https://gcc.gnu.org/bugzilla/xmlrpc.cgi \
        query \
        --product=gcc \
        --component="$component" \
        --status=UNCONFIRMED,NEW,ASSIGNED,REOPENED,WAITING,SUSPENDED \
        --summary="$summary" \
        --outputformat='%{bug_id}\t%{short_desc}' |
        awk -F '\t' -v summary="$summary" '$2 == summary { print $1; exit }'
}

find_existing_issue_url() {
    local title="$1"

    gh issue list \
        --repo "$ISSUE_REPO" \
        --limit 500 \
        --search "$title in:title" \
        --json title,url \
        --jq ".[] | select(.title == \"$title\") | .url" |
        head -n1
}

create_issue() {
    local title="$1"
    local body_file="$2"
    shift 2
    gh issue create --repo "$ISSUE_REPO" --title "$title" --body-file "$body_file" "$@"
}

write_readme() {
    local bug_id="$1"
    local summary="$2"
    local issue_url="$3"
    local readme="$ROOT/pr/$bug_id/README.md"

    mkdir -p "$ROOT/pr/$bug_id"
    cat > "$readme" <<EOF
# Bug $bug_id: $summary

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$bug_id
- **GitHub issue:** $issue_url
- **Status:** OPEN

## Technical notes

- Created from the 2026-04-18 testsuite provenance audit.
- See the reviewed Bugzilla draft for affected files and suggested cleanup.
EOF
}

process_slug() {
    local slug="$1"
    local component summary gh_suffix draft_file bug_id issue_title issue_url tmp_body
    local -a labels=()
    local -a gh_args=()

    case "$slug" in
        go-test)
            component="go"
            summary="go: imported go.test subtree points to missing local LICENSE companion"
            gh_suffix="go.test subtree imported into GCC testsuite lacks local license companion"
            labels=("bug" "needs-triage" "complexity:medium")
            draft_file="$ROOT/.provenance/bugzilla/go-test.txt"
            ;;
        *)
            echo "Unknown slug: $slug" >&2
            exit 2
            ;;
    esac

    bug_id="${BUGZILLA_ID:-}"
    if [[ -z "$bug_id" ]]; then
        bug_id="$(find_existing_bug "$component" "$summary" || true)"
    fi

    if [[ -z "$bug_id" ]]; then
        echo "No matching Bugzilla bug found for $slug." >&2
        echo "Reviewed draft: $draft_file" >&2
        echo "Create it manually first with:" >&2
        echo "  GCC_BUGZILLA_MANUAL_CONFIRM=1 scripts/gcc-bugzilla.sh new $component '$summary' $draft_file" >&2
        [[ "$EXECUTE" -eq 1 ]] && exit 2
        return 0
    fi

    issue_title="PR${bug_id}: $gh_suffix"
    issue_url="$(find_existing_issue_url "$issue_title" || true)"

    if [[ -z "$issue_url" && "$EXECUTE" -eq 1 ]]; then
        tmp_body="$(mktemp)"
        {
            printf 'Upstream GCC Bugzilla: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=%s\n\n' "$bug_id"
            cat "$draft_file"
        } > "$tmp_body"
        for label in "${labels[@]}"; do
            gh_args+=(--label "$label")
        done
        issue_url="$(create_issue "$issue_title" "$tmp_body" "${gh_args[@]}")"
        rm -f "$tmp_body"
    fi

    if [[ "$EXECUTE" -eq 1 ]]; then
        write_readme "$bug_id" "$summary" "$issue_url"
        python3 "$ROOT/scripts/gcc-workflow.py" sync-metadata "$bug_id"
        echo "tracked $slug as bug $bug_id ($issue_url)"
    else
        echo "DRY-RUN $slug -> https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$bug_id"
        if [[ -n "$issue_url" ]]; then
            echo "DRY-RUN reusing GitHub issue $issue_url"
        else
            echo "DRY-RUN would create GitHub issue: $issue_title"
        fi
    fi
}

args=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --execute)
            EXECUTE=1
            ;;
        --bugzilla-id)
            BUGZILLA_ID="${2:-}"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            args+=("$1")
            ;;
    esac
    shift
done

if [[ ${#args[@]} -eq 0 ]]; then
    args=("go-test")
fi

for slug in "${args[@]}"; do
    process_slug "$slug"
done
