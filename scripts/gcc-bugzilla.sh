#!/bin/bash
# gcc-bugzilla.sh - Query and interact with GCC Bugzilla
#
# Usage:
#   gcc-bugzilla.sh info <pr-number>                          # Show bug info
#   gcc-bugzilla.sh search <term>                             # Search fortran bugs
#   gcc-bugzilla.sh regressions                               # List open fortran regressions
#   gcc-bugzilla.sh comment <pr-number> <text>                  # Post a comment
#   gcc-bugzilla.sh attach <pr-number> <file> [desc] [comment]  # Attach with optional comment
#   gcc-bugzilla.sh login                                     # Login to GCC Bugzilla
#   gcc-bugzilla.sh submit <pr-number> [branch] [--execute]   # Submit generated packet
#
# Requires: python-bugzilla (pip install python-bugzilla)

set -euo pipefail

BUGZILLA_URL="https://gcc.gnu.org/bugzilla/xmlrpc.cgi"
BZ="bugzilla --bugzilla=$BUGZILLA_URL"
AUTO_CC_DEFAULT="${GCC_BUGZILLA_AUTO_CC:-albert@tugraz.at,jvdelisle@gcc.gnu.org}"

usage() {
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  info <pr-number>                          Show bug status, summary, and details"
    echo "  search <term>                             Search open fortran bugs by summary text"
    echo "  regressions                               List all open fortran regressions"
    echo "  comment <pr-number> <text>                  Post a comment on a bug"
    echo "  attach <pr-number> <file> [desc] [comment]  Attach a file (requires login)"
    echo "  ensure-cc <pr-number> [email[,email...]]   Add CC entries to a bug"
    echo "  login                                     Login to GCC Bugzilla (saves token)"
    echo "  submit <pr-number> [branch] [--execute]   Submit generated workflow packet"
    echo ""
    echo "Examples:"
    echo "  $0 info 124235"
    echo "  $0 search 'ICE in fold_convert'"
    echo "  $0 regressions"
    echo "  $0 attach 123280 pr/123280/0001-fix.patch"
    echo "  $0 attach 123280 pr/123280/0001-fix.patch 'Proposed patch' 'Fixes the ICE by...'"
    echo "  $0 comment 124512 'Reproduced on cfarm428...'"
    echo "  $0 ensure-cc 108382"
    echo "  $0 submit 120723 gcc-15 --execute"
    exit 1
}

cmd_submit() {
    local pr="$1"
    shift || true
    exec python3 "$(dirname "$0")/gcc-workflow.py" submit-bugzilla "$pr" "$@"
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

cmd_comment() {
    local pr="$1"
    local text="$2"
    local auto_cc="$AUTO_CC_DEFAULT"

    echo "Posting comment on bug $pr..."
    echo ""
    echo "  Bug:     https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo ""
    echo "--- Comment text ---"
    echo "$text"
    echo "--- End ---"
    echo ""
    local confirm="${GCC_BUGZILLA_ASSUME_YES:-}"
    if [[ -z "$confirm" ]]; then
        read -rp "Proceed? [y/N] " confirm
    fi
    if [[ "$confirm" != "1" && "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi

    python3 - "$pr" "$text" "$auto_cc" <<'PYEOF'
import sys, bugzilla
pr, text, auto_cc = sys.argv[1], sys.argv[2], sys.argv[3]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
bug = bz.getbug(int(pr))
bz.update_bugs(int(pr), bz.build_update(comment=text, cc_add=[email for email in auto_cc.split(",") if email]))
print(f"Comment posted on bug {pr}")
print(f"https://gcc.gnu.org/bugzilla/show_bug.cgi?id={pr}")
PYEOF
    echo "Done."
}

cmd_attach() {
    local pr="$1"
    local file="$2"
    local desc="${3:-$(basename "$file")}"
    local comment="${4:-}"
    local auto_cc="$AUTO_CC_DEFAULT"

    if [[ ! -f "$file" ]]; then
        echo "Error: file not found: $file" >&2
        exit 1
    fi

    file="$(realpath "$file")"

    echo "Attaching '$file' to bug $pr..."
    echo ""
    echo "  Bug:     https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo "  File:    $file"
    echo "  Desc:    $desc"
    [[ -n "$comment" ]] && echo "  Comment: $comment"
    echo ""
    local confirm="${GCC_BUGZILLA_ASSUME_YES:-}"
    if [[ -z "$confirm" ]]; then
        read -rp "Proceed? [y/N] " confirm
    fi
    if [[ "$confirm" != "1" && "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi

    python3 - "$pr" "$file" "$desc" "$comment" "$auto_cc" <<'PYEOF'
import sys, bugzilla
pr, path, desc, comment, auto_cc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
kwargs = dict(content_type="text/plain", is_patch=True)
if comment:
    kwargs["comment"] = comment
att_id = bz.attachfile(int(pr), path, desc, **kwargs)
bz.update_bugs(int(pr), bz.build_update(cc_add=[email for email in auto_cc.split(",") if email]))
print(f"Attachment ID: {att_id}")
print(f"https://gcc.gnu.org/bugzilla/show_bug.cgi?id={pr}")
PYEOF
    echo "Done."
}

cmd_ensure_cc() {
    local pr="$1"
    local cc_list="${2:-$AUTO_CC_DEFAULT}"

    echo "Adding CC entries on bug $pr..."
    echo ""
    echo "  Bug: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo "  CC:  $cc_list"
    echo ""
    local confirm="${GCC_BUGZILLA_ASSUME_YES:-}"
    if [[ -z "$confirm" ]]; then
        read -rp "Proceed? [y/N] " confirm
    fi
    if [[ "$confirm" != "1" && "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi

    python3 - "$pr" "$cc_list" <<'PYEOF'
import sys, bugzilla
pr, cc_list = sys.argv[1], sys.argv[2]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
bz.update_bugs(int(pr), bz.build_update(cc_add=[email for email in cc_list.split(",") if email]))
print(f"Updated CC on bug {pr}")
print(f"https://gcc.gnu.org/bugzilla/show_bug.cgi?id={pr}")
PYEOF
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
    comment)
        [[ $# -lt 3 ]] && { echo "Error: missing PR number or comment text"; usage; }
        cmd_comment "$2" "$3"
        ;;
    attach)
        [[ $# -lt 3 ]] && { echo "Error: missing PR number or file"; usage; }
        cmd_attach "$2" "$3" "${4:-}" "${5:-}"
        ;;
    ensure-cc)
        [[ $# -lt 2 ]] && { echo "Error: missing PR number"; usage; }
        cmd_ensure_cc "$2" "${3:-}"
        ;;
    login)
        cmd_login
        ;;
    submit)
        [[ $# -lt 2 ]] && { echo "Error: missing PR number"; usage; }
        cmd_submit "$2" "${@:3}"
        ;;
    *)
        echo "Unknown command: $1" >&2
        usage
        ;;
esac
