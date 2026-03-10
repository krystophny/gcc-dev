#!/bin/bash
# gcc-bugzilla.sh - Query and interact with GCC Bugzilla
#
# Usage:
#   gcc-bugzilla.sh info <pr-number>           # Show bug info
#   gcc-bugzilla.sh search <term>              # Search fortran bugs
#   gcc-bugzilla.sh regressions                # List open fortran regressions
#   gcc-bugzilla.sh attach <pr-number> <file>  # Attach a file (requires login)
#   gcc-bugzilla.sh login                      # Login to GCC Bugzilla
#
# Requires: python-bugzilla (pip install python-bugzilla)

set -euo pipefail

BUGZILLA_URL="https://gcc.gnu.org/bugzilla/xmlrpc.cgi"
BZ="bugzilla --bugzilla=$BUGZILLA_URL"

usage() {
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  info <pr-number>            Show bug status, summary, and details"
    echo "  search <term>               Search open fortran bugs by summary text"
    echo "  regressions                 List all open fortran regressions"
    echo "  attach <pr-number> <file>   Attach a file to the bug (requires login)"
    echo "  login                       Login to GCC Bugzilla (saves token)"
    echo ""
    echo "Examples:"
    echo "  $0 info 124235"
    echo "  $0 search 'ICE in fold_convert'"
    echo "  $0 regressions"
    echo "  $0 attach 123280 pr/123280/0001-fix.patch"
    exit 1
}

cmd_info() {
    local pr="$1"
    echo "=== Bug $pr ==="
    $BZ query --bug_id="$pr" \
        --outputformat="%{bug_id} [%{bug_status}] %{short_desc}"
    echo ""
    echo "URL: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo ""
    echo "=== Details ==="
    $BZ query --bug_id="$pr" \
        --outputformat="Status:    %{bug_status} %{resolution}
Component: %{component}
Assignee:  %{assigned_to}
CC:        %{cc}
Blocks:    %{blocks}
Depends:   %{depends_on}"
}

cmd_search() {
    local term="$1"
    $BZ query \
        --product=gcc \
        --component=fortran \
        --status=UNCONFIRMED,NEW,ASSIGNED,SUSPENDED,WAITING,REOPENED \
        --summary="$term" \
        --outputformat="%{bug_id} [%{bug_status}] %{short_desc}"
}

cmd_regressions() {
    $BZ query \
        --product=gcc \
        --component=fortran \
        --status=UNCONFIRMED,NEW,ASSIGNED,SUSPENDED,WAITING,REOPENED \
        --summary="regression" \
        --outputformat="%{bug_id} [%{bug_status}] %{short_desc}"
}

cmd_attach() {
    local pr="$1"
    local file="$2"

    if [[ ! -f "$file" ]]; then
        echo "Error: file not found: $file" >&2
        exit 1
    fi

    local desc
    desc="$(basename "$file")"

    echo "Attaching '$file' to bug $pr as '$desc'..."
    echo ""
    echo "  Bug: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo "  File: $file"
    echo ""
    read -rp "Proceed? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi

    $BZ attach --file="$file" --desc="$desc" --type="text/plain" "$pr"
    echo "Done."
}

cmd_login() {
    echo "Logging in to GCC Bugzilla..."
    echo "You will be prompted for your username and password."
    $BZ login
}

[[ $# -lt 1 ]] && usage

case "$1" in
    info)
        [[ $# -lt 2 ]] && { echo "Error: missing PR number"; usage; }
        cmd_info "$2"
        ;;
    search)
        [[ $# -lt 2 ]] && { echo "Error: missing search term"; usage; }
        cmd_search "$2"
        ;;
    regressions)
        cmd_regressions
        ;;
    attach)
        [[ $# -lt 3 ]] && { echo "Error: missing PR number or file"; usage; }
        cmd_attach "$2" "$3"
        ;;
    login)
        cmd_login
        ;;
    *)
        echo "Unknown command: $1" >&2
        usage
        ;;
esac
