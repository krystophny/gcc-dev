#!/bin/bash
# sync-issues.sh - Align GitHub issues with upstream GCC master and Bugzilla status
#
# Usage:
#   sync-issues.sh fetch                       Fetch upstream/master in gcc/
#   sync-issues.sh check-merged [--pr NUMBER]  Find PRs merged on upstream/master
#   sync-issues.sh bugzilla-status [--pr N]    Query Bugzilla status for open issues
#   sync-issues.sh regressions                 Find untracked Bugzilla regressions
#   sync-issues.sh close-merged [--dry-run] [--yes]  Close merged issues
#   sync-issues.sh full [--yes]                Run all subcommands with summary
#
# Requires: gh, git, jq, python3, scripts/gcc-bugzilla.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GCC_DIR="$REPO_ROOT/gcc"
BUGZILLA="$SCRIPT_DIR/gcc-bugzilla.sh"
# Issues live on the downstream fork, not the meta-repo.
GH_ISSUE_REPO="${GH_ISSUE_REPO:-lazy-fortran/gcc}"

die() { echo "ERROR: $*" >&2; exit 1; }

# Retry a command once on failure (for network resilience).
retry_once() {
    "$@" 2>/dev/null || "$@"
}

# Extract PR number from a GitHub issue title.
# Handles: "PR12345: ...", "Bug 12345: ...", "pr12345: ..."
extract_pr() {
    local title="$1"
    if [[ "$title" =~ ^[Pp][Rr]([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    elif [[ "$title" =~ ^[Bb]ug[[:space:]]+([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

# List open GitHub issues as JSON array of {number, title, pr}.
# Caches result for the duration of one invocation via a tempfile.
OPEN_ISSUES_CACHE=""
list_open_issues() {
    if [[ -n "$OPEN_ISSUES_CACHE" && -f "$OPEN_ISSUES_CACHE" ]]; then
        cat "$OPEN_ISSUES_CACHE"
        return
    fi
    OPEN_ISSUES_CACHE="$(mktemp /tmp/sync-issues-cache.XXXXXX)"
    retry_once gh issue list --repo "$GH_ISSUE_REPO" --state open --limit 500 --json number,title \
        | python3 -c "
import json, re, sys
issues = json.load(sys.stdin)
result = []
for iss in issues:
    title = iss['title']
    m = re.match(r'^[Pp][Rr](\d+)', title) or re.match(r'^[Bb]ug\s+(\d+)', title)
    if m:
        result.append({'number': iss['number'], 'title': title, 'pr': int(m.group(1))})
json.dump(result, sys.stdout)
" > "$OPEN_ISSUES_CACHE"
    cat "$OPEN_ISSUES_CACHE"
}

cleanup_cache() {
    if [[ -n "$OPEN_ISSUES_CACHE" && -f "$OPEN_ISSUES_CACHE" ]]; then
        rm -f "$OPEN_ISSUES_CACHE"
    fi
}
trap cleanup_cache EXIT

# ---- Subcommands ----

cmd_fetch() {
    echo "Fetching upstream/master in gcc/..."
    git -C "$GCC_DIR" fetch upstream
    local head
    head="$(git -C "$GCC_DIR" rev-parse --short upstream/master)"
    echo "upstream/master is now at $head"
}

# Search upstream/master log for commits mentioning a PR number in
# Fortran-related paths. Returns lines: "<hash> <subject>".
find_upstream_commits() {
    local pr="$1"
    git -C "$GCC_DIR" log upstream/master --all-match \
        --grep="$pr" --oneline \
        -- gcc/fortran/ 'gcc/testsuite/gfortran.dg/' libgomp/ \
        2>/dev/null || true
}

cmd_check_merged() {
    local filter_pr=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pr) filter_pr="$2"; shift 2 ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    local issues
    issues="$(list_open_issues)"

    local found=0
    echo ""
    printf "%-8s %-8s %-12s %s\n" "PR" "ISSUE" "COMMIT" "SUBJECT"
    printf "%-8s %-8s %-12s %s\n" "------" "------" "----------" "-------"

    local pr_list
    pr_list="$(echo "$issues" | python3 -c "import json,sys; [print(f'{i[\"pr\"]} {i[\"number\"]}') for i in json.load(sys.stdin)]")"

    while read -r pr issue_num; do
        [[ -z "$pr" ]] && continue
        if [[ -n "$filter_pr" && "$pr" != "$filter_pr" ]]; then
            continue
        fi
        local commits
        commits="$(find_upstream_commits "$pr")"
        if [[ -n "$commits" ]]; then
            while IFS= read -r line; do
                local hash subject
                hash="${line%% *}"
                subject="${line#* }"
                printf "%-8s %-8s %-12s %s\n" "$pr" "#$issue_num" "$hash" "$subject"
                found=1
            done <<< "$commits"
        fi
    done <<< "$pr_list"

    if [[ "$found" -eq 0 ]]; then
        echo "(none found)"
    fi
}

cmd_bugzilla_status() {
    local filter_pr=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pr) filter_pr="$2"; shift 2 ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    local issues
    issues="$(list_open_issues)"

    echo ""
    printf "%-8s %-8s %-14s %-30s %s\n" "PR" "ISSUE" "BZ STATUS" "ASSIGNEE" "TITLE"
    printf "%-8s %-8s %-14s %-30s %s\n" "------" "------" "------------" "----------------------------" "-----"

    local issue_lines
    issue_lines="$(echo "$issues" | python3 -c "import json,sys; [print(f'{i[\"pr\"]} {i[\"number\"]} {i[\"title\"]}') for i in json.load(sys.stdin)]")"

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local pr issue_num title
        pr="$(echo "$line" | awk '{print $1}')"
        issue_num="$(echo "$line" | awk '{print $2}')"
        title="$(echo "$line" | cut -d' ' -f3-)"
        if [[ -n "$filter_pr" && "$pr" != "$filter_pr" ]]; then
            continue
        fi
        local bz_info
        bz_info="$(retry_once "$BUGZILLA" info "$pr" 2>/dev/null)" || {
            printf "%-8s %-8s %-14s %-30s %s\n" "$pr" "#$issue_num" "QUERY_FAILED" "" "$title"
            continue
        }
        local status assignee
        status="$(echo "$bz_info" | sed -n 's/^Status:[[:space:]]*//p' | awk '{print $1}')"
        assignee="$(echo "$bz_info" | sed -n 's/^Assignee:[[:space:]]*//p')"
        printf "%-8s %-8s %-14s %-30s %s\n" "$pr" "#$issue_num" "$status" "$assignee" "$title"
    done <<< "$issue_lines"
}

cmd_regressions() {
    echo "Querying Bugzilla for open Fortran regressions..."
    local bz_regressions
    bz_regressions="$(retry_once "$BUGZILLA" regressions 2>/dev/null)" || die "Bugzilla query failed"

    local issues
    issues="$(list_open_issues)"
    local tracked_prs
    tracked_prs="$(echo "$issues" | python3 -c "import json,sys; print(' '.join(str(i['pr']) for i in json.load(sys.stdin)))")"

    echo ""
    echo "=== Untracked Bugzilla Regressions ==="
    printf "%-8s %-14s %s\n" "PR" "STATUS" "SUMMARY"
    printf "%-8s %-14s %s\n" "------" "------------" "-------"

    local untracked=0
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local bz_pr bz_status bz_summary
        bz_pr="$(echo "$line" | awk '{print $1}')"
        bz_status="$(echo "$line" | sed 's/^[0-9]* \[//' | sed 's/\].*//')"
        bz_summary="$(echo "$line" | sed 's/^[0-9]* \[[^]]*\] //')"
        local is_tracked=0
        for tp in $tracked_prs; do
            if [[ "$tp" == "$bz_pr" ]]; then
                is_tracked=1
                break
            fi
        done
        if [[ "$is_tracked" -eq 0 ]]; then
            printf "%-8s %-14s %s\n" "$bz_pr" "$bz_status" "$bz_summary"
            untracked=$((untracked + 1))
        fi
    done <<< "$bz_regressions"

    echo ""
    echo "Total untracked regressions: $untracked"
}

cmd_close_merged() {
    local dry_run=0
    local auto_yes=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run) dry_run=1; shift ;;
            --yes) auto_yes=1; shift ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    local issues
    issues="$(list_open_issues)"

    local to_close=""
    local count=0

    while IFS= read -r line; do
        local pr issue_num
        pr="$(echo "$line" | awk '{print $1}')"
        issue_num="$(echo "$line" | awk '{print $2}')"
        local commits
        commits="$(find_upstream_commits "$pr")"
        if [[ -n "$commits" ]]; then
            local first_commit first_hash first_subject
            first_commit="$(echo "$commits" | head -1)"
            first_hash="${first_commit%% *}"
            first_subject="${first_commit#* }"
            local full_hash
            full_hash="$(git -C "$GCC_DIR" rev-parse "$first_hash" 2>/dev/null || echo "$first_hash")"
            local descr
            descr="$(cd "$GCC_DIR" && git gcc-descr "$full_hash" 2>/dev/null || echo "$full_hash")"
            to_close="${to_close}${pr} ${issue_num} ${full_hash} ${descr}
"
            count=$((count + 1))
        fi
    done < <(echo "$issues" | python3 -c "import json,sys; [print(f'{i[\"pr\"]} {i[\"number\"]}') for i in json.load(sys.stdin)]")

    if [[ "$count" -eq 0 ]]; then
        echo "No merged issues to close."
        return
    fi

    echo ""
    echo "=== Issues to Close ==="
    printf "%-8s %-8s %-40s %s\n" "PR" "ISSUE" "COMMIT" "GCC DESCR"
    printf "%-8s %-8s %-40s %s\n" "------" "------" "--------------------------------------" "---------"
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local pr issue_num hash descr
        pr="$(echo "$line" | awk '{print $1}')"
        issue_num="$(echo "$line" | awk '{print $2}')"
        hash="$(echo "$line" | awk '{print $3}')"
        descr="$(echo "$line" | cut -d' ' -f4-)"
        printf "%-8s %-8s %-40s %s\n" "$pr" "#$issue_num" "$hash" "$descr"
    done <<< "$to_close"

    if [[ "$dry_run" -eq 1 ]]; then
        echo ""
        echo "(dry run -- no issues closed)"
        return
    fi

    if [[ "$auto_yes" -ne 1 ]]; then
        echo ""
        read -rp "Close $count issue(s)? [y/N] " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            echo "Aborted."
            return
        fi
    fi

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local pr issue_num hash descr
        pr="$(echo "$line" | awk '{print $1}')"
        issue_num="$(echo "$line" | awk '{print $2}')"
        hash="$(echo "$line" | awk '{print $3}')"
        descr="$(echo "$line" | cut -d' ' -f4-)"
        local comment
        comment="Merged upstream: ${descr}
https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=${hash}"
        echo "Closing #${issue_num} (PR${pr})..."
        retry_once gh issue close "$issue_num" --repo "$GH_ISSUE_REPO" --comment "$comment"
    done <<< "$to_close"

    echo "Closed $count issue(s)."
}

cmd_full() {
    local close_args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --yes) close_args+=(--yes); shift ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    echo "========================================"
    echo "  sync-issues: full sync"
    echo "========================================"
    echo ""

    echo "--- Step 1: Fetch upstream ---"
    cmd_fetch
    echo ""

    echo "--- Step 2: Check for merged PRs ---"
    cmd_check_merged
    echo ""

    echo "--- Step 3: Close merged issues ---"
    cmd_close_merged "${close_args[@]}"
    echo ""

    echo "--- Step 4: Untracked regressions ---"
    cmd_regressions
    echo ""

    echo "--- Step 5: Bugzilla status for open issues ---"
    cmd_bugzilla_status
    echo ""

    echo "========================================"
    echo "  sync-issues: complete"
    echo "========================================"
}

usage() {
    cat <<'EOF'
Usage: sync-issues.sh <command> [options]

Commands:
  fetch                        Fetch upstream/master in gcc/
  check-merged [--pr NUMBER]   Find PRs with upstream commits
  bugzilla-status [--pr N]     Query Bugzilla status for open issues
  regressions                  Find untracked Bugzilla regressions
  close-merged [--dry-run] [--yes]  Close GitHub issues for merged PRs
  full [--yes]                 Run all subcommands with summary report

Options:
  --pr NUMBER    Restrict to a single PR number
  --dry-run      Show what would be closed without closing
  --yes          Skip confirmation prompt

Examples:
  sync-issues.sh fetch
  sync-issues.sh check-merged --pr 123280
  sync-issues.sh close-merged --dry-run
  sync-issues.sh full --yes
EOF
    exit 1
}

[[ $# -lt 1 ]] && usage

case "$1" in
    fetch)           shift; cmd_fetch "$@" ;;
    check-merged)    shift; cmd_check_merged "$@" ;;
    bugzilla-status) shift; cmd_bugzilla_status "$@" ;;
    regressions)     shift; cmd_regressions "$@" ;;
    close-merged)    shift; cmd_close_merged "$@" ;;
    full)            shift; cmd_full "$@" ;;
    -h|--help|help)  usage ;;
    *)               die "Unknown command: $1"; usage ;;
esac
