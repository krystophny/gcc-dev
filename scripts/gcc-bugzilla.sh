#!/bin/bash
# gcc-bugzilla.sh - Query and interact with GCC Bugzilla
#
# Usage:
#   gcc-bugzilla.sh info <pr-number>                          # Show bug info
#   gcc-bugzilla.sh comments <pr-number>                      # Show all comments
#   gcc-bugzilla.sh attachments <pr-number>                   # List attachments
#   gcc-bugzilla.sh download <pr-number> [outdir]             # Download all patches
#   gcc-bugzilla.sh search <term>                             # Search fortran bugs
#   gcc-bugzilla.sh regressions                               # List open fortran regressions
#   gcc-bugzilla.sh new <component> <summary> <comment-file> [version]
#                                                             # Create a new GCC Bugzilla bug
#   gcc-bugzilla.sh comment <pr-number> <text>                  # Post a comment
#   gcc-bugzilla.sh comment-file <pr-number> <file>             # Post a draft comment from file
#   gcc-bugzilla.sh reply <pr-number> <comment-number> <text>   # Quote-reply to a comment
#   gcc-bugzilla.sh reply-file <pr-number> <comment-number> <file>
#                                                             # Quote-reply using text from file
#   gcc-bugzilla.sh attach [--obsolete <id[,id...]>] [--comment-file <file>] <pr-number> <file> [desc] [comment]
#                                                             # Attach with optional comment and supersede older attachments
#   gcc-bugzilla.sh login                                     # Login to GCC Bugzilla
#   gcc-bugzilla.sh submit <pr-number> [branch] [--execute]   # Submit generated packet
#
# Requires: python-bugzilla (pip install python-bugzilla)

set -euo pipefail

BUGZILLA_URL="https://gcc.gnu.org/bugzilla/xmlrpc.cgi"
BZ="bugzilla --bugzilla=$BUGZILLA_URL"
AUTO_CC_DEFAULT="${GCC_BUGZILLA_AUTO_CC:-albert@tugraz.at,jvdelisle@gcc.gnu.org}"

default_new_version() {
    python3 - <<'PYEOF'
import re, bugzilla
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
prod = bz._proxy.Product.get({"names": ["gcc"]})["products"][0]
versions = []
for item in prod["versions"]:
    if not item.get("is_active"):
        continue
    name = item["name"]
    if re.fullmatch(r"\d+\.0", name):
        versions.append((int(name.split(".", 1)[0]), name))
if versions:
    print(max(versions)[1])
else:
    print("16.0")
PYEOF
}

require_manual_bugzilla_write_auth() {
    local action="$1"

    if [[ "${GCC_BUGZILLA_MANUAL_CONFIRM:-}" != "1" ]]; then
        echo "Refusing Bugzilla write operation: $action" >&2
        echo "Set GCC_BUGZILLA_MANUAL_CONFIRM=1 only after manual review and explicit user confirmation." >&2
        exit 2
    fi
}

confirm_bugzilla_write() {
    local action="$1"
    local confirm="${GCC_BUGZILLA_ASSUME_YES:-}"

    require_manual_bugzilla_write_auth "$action"

    if [[ -z "$confirm" ]]; then
        read -rp "Proceed with Bugzilla write '$action'? [y/N] " confirm
    fi
    if [[ "$confirm" != "1" && "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
}

read_text_file_or_die() {
    local path="$1"

    if [[ ! -f "$path" ]]; then
        echo "Error: text file not found: $path" >&2
        exit 1
    fi
    cat "$path"
}

usage() {
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  info <pr-number>                          Show bug status, summary, and details"
    echo "  comments <pr-number>                      Show all comments on a bug"
    echo "  attachments <pr-number>                   List all attachments on a bug"
    echo "  download <pr-number> [outdir]             Download all patch attachments"
    echo "  search <term>                             Search open fortran bugs by summary text"
    echo "  regressions                               List all open fortran regressions"
    echo "  new <component> <summary> <comment-file> [version]"
    echo "                                              Create a new GCC Bugzilla bug"
    echo "  comment <pr-number> <text>                  Post a comment on a bug"
    echo "  comment-file <pr-number> <file>             Post a reviewed draft comment from file"
    echo "  reply <pr-number> <comment#> <text>         Quote-reply to a specific comment"
    echo "  reply-file <pr-number> <comment#> <file>    Quote-reply using text from file"
    echo "  attach [--obsolete <id[,id...]>] [--comment-file <file>] <pr-number> <file> [desc] [comment]"
    echo "                                              Attach a file (requires login)"
    echo "  ensure-cc <pr-number> [email[,email...]]   Add CC entries to a bug"
    echo "  login                                     Login to GCC Bugzilla (saves token)"
    echo "  submit <pr-number> [branch] [--execute]   Submit generated workflow packet"
    echo ""
    echo "Examples:"
    echo "  $0 info 124235"
    echo "  $0 search 'ICE in fold_convert'"
    echo "  $0 regressions"
    echo "  $0 new testsuite 'testsuite: imported subtree lacks retained notice' /tmp/body.txt"
    echo "  $0 comment-file 124512 pr/124512/submission/bugzilla-comment.txt"
    echo "  $0 reply-file 124661 7 /tmp/reply.txt"
    echo "  $0 attach 123280 pr/123280/0001-fix.patch"
    echo "  $0 attach --comment-file pr/123280/submission/bugzilla-comment.txt 123280 pr/123280/0001-fix.patch"
    echo "  $0 attach --obsolete 64064 --comment-file /tmp/v2-note.txt 102333 pr/102333/0002-fix.patch 'v2 patch'"
    echo "  $0 comment 124512 'Reproduced on cfarm428...'"
    echo "  $0 reply 124661 7 'Your approach with find_tree is cleaner.'"
    echo "  $0 ensure-cc 108382"
    echo "  $0 comments 123280"
    echo "  $0 attachments 123280"
    echo "  $0 download 123280 pr/123280/upstream-patches"
    echo "  $0 submit 120723 gcc-15 --execute"
    exit 1
}

cmd_submit() {
    local pr="$1"
    shift || true
    local arg

    for arg in "$@"; do
        if [[ "$arg" == "--execute" ]]; then
            require_manual_bugzilla_write_auth "submit Bugzilla packet for bug $pr"
            break
        fi
    done
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

cmd_comments() {
    local pr="$1"
    python3 - "$pr" <<'PYEOF'
import sys, bugzilla
pr = sys.argv[1]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
bug = bz.getbug(int(pr))
comments = bug.getcomments()
for i, c in enumerate(comments):
    author = c.get("creator", c.get("author", "unknown"))
    date = c.get("creation_time", "unknown")
    text = c.get("text", "")
    print(f"--- Comment #{i} by {author} ({date}) ---")
    print(text)
    print()
PYEOF
}

cmd_attachments() {
    local pr="$1"
    python3 - "$pr" <<'PYEOF'
import sys, bugzilla
pr = sys.argv[1]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
atts = bz._proxy.Bug.attachments({"ids": [int(pr)]})
bug_atts = atts.get("bugs", {}).get(str(pr), atts.get("bugs", {}).get(int(pr), []))
if not bug_atts:
    print("No attachments.")
    sys.exit(0)
for att in bug_atts:
    obs = " [OBSOLETE]" if att["is_obsolete"] else ""
    patch = " [PATCH]" if att["is_patch"] else ""
    data = att.get("data")
    if data is None:
        size = att.get("size", "?")
    elif hasattr(data, "data"):
        size = len(data.data)
    elif isinstance(data, (bytes, str)):
        size = len(data)
    else:
        size = "?"
    print(f"ID {att['id']}: {att['file_name']}{patch}{obs} ({size} bytes) - {att.get('summary', att.get('description', 'N/A'))} by {att['creator']}")
PYEOF
}

cmd_download() {
    local pr="$1"
    local outdir="${2:-pr/$pr/upstream-patches}"
    mkdir -p "$outdir"
    python3 - "$pr" "$outdir" <<'PYEOF'
import sys, os, base64, bugzilla
pr, outdir = sys.argv[1], sys.argv[2]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
atts = bz._proxy.Bug.attachments({"ids": [int(pr)]})
bug_atts = atts.get("bugs", {}).get(str(pr), atts.get("bugs", {}).get(int(pr), []))
patches = [a for a in bug_atts if a["is_patch"] and not a["is_obsolete"]]
if not patches:
    print("No non-obsolete patch attachments found.")
    all_atts = [a for a in bug_atts if a["is_patch"]]
    if all_atts:
        print(f"({len(all_atts)} obsolete patch(es) skipped; use 'attachments' to see all)")
    sys.exit(0)
for att in patches:
    data = att.get("data")
    if data is None:
        print(f"  Skipping {att['file_name']}: no data returned")
        continue
    if isinstance(data, str):
        content = base64.b64decode(data)
    elif hasattr(data, "data"):
        content = data.data if isinstance(data.data, bytes) else base64.b64decode(data.data)
    else:
        content = bytes(data) if not isinstance(data, bytes) else data
    fname = f"{att['id']:05d}-{att['file_name']}"
    path = os.path.join(outdir, fname)
    with open(path, "wb") as f:
        f.write(content)
    print(f"  {path} ({len(content)} bytes)")
print(f"Downloaded {len(patches)} patch(es) to {outdir}/")
PYEOF
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

cmd_new() {
    local component="$1"
    local summary="$2"
    local comment_file="$3"
    local version="${4:-$(default_new_version)}"

    if [[ ! -f "$comment_file" ]]; then
        echo "Error: comment file not found: $comment_file" >&2
        exit 1
    fi

    local comment
    comment="$(cat "$comment_file")"

    echo "Creating new GCC Bugzilla bug..."
    echo ""
    echo "  Product:   gcc"
    echo "  Component: $component"
    echo "  Version:   $version"
    echo "  Summary:   $summary"
    echo "  Comment:   $comment_file"
    echo ""
    confirm_bugzilla_write "create new bug '$summary'"

    local bug_id
    bug_id="$($BZ new -p gcc -v "$version" -c "$component" -t "$summary" -l "$comment" -i)"
    echo "Created bug $bug_id"
    echo "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$bug_id"
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
    confirm_bugzilla_write "post comment to bug $pr"

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

cmd_comment_file() {
    local pr="$1"
    local path="$2"
    local text

    text="$(read_text_file_or_die "$path")"
    cmd_comment "$pr" "$text"
}

cmd_reply() {
    local pr="$1"
    local comment_num="$2"
    local text="$3"
    local auto_cc="$AUTO_CC_DEFAULT"

    # Build the full reply text: quote header + quoted comment + reply
    local full_text
    full_text=$(python3 - "$pr" "$comment_num" "$text" <<'PYEOF'
import sys, bugzilla
pr, cnum, reply = sys.argv[1], int(sys.argv[2]), sys.argv[3]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
bug = bz.getbug(int(pr))
comments = bug.getcomments()
if cnum < 0 or cnum >= len(comments):
    print(f"Error: comment #{cnum} does not exist (bug has {len(comments)} comments)", file=sys.stderr)
    sys.exit(1)
c = comments[cnum]
author = c.get("creator", c.get("author", "unknown"))
body = c.get("text", "")
quoted = "\n".join(f"> {line}" for line in body.splitlines())
header = f"(In reply to {author} from comment #{cnum})"
print(f"{header}\n{quoted}\n\n{reply}")
PYEOF
    ) || exit 1

    echo "Posting quote-reply on bug $pr (quoting comment #$comment_num)..."
    echo ""
    echo "  Bug:     https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo ""
    echo "--- Comment text ---"
    echo "$full_text"
    echo "--- End ---"
    echo ""
    confirm_bugzilla_write "post reply to bug $pr"

    python3 - "$pr" "$full_text" "$auto_cc" <<'PYEOF'
import sys, bugzilla
pr, text, auto_cc = sys.argv[1], sys.argv[2], sys.argv[3]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
bz.update_bugs(int(pr), bz.build_update(comment=text, cc_add=[email for email in auto_cc.split(",") if email]))
print(f"Comment posted on bug {pr}")
print(f"https://gcc.gnu.org/bugzilla/show_bug.cgi?id={pr}")
PYEOF
    echo "Done."
}

cmd_reply_file() {
    local pr="$1"
    local comment_num="$2"
    local path="$3"
    local text

    text="$(read_text_file_or_die "$path")"
    cmd_reply "$pr" "$comment_num" "$text"
}

cmd_attach() {
    local obsolete_ids=""
    local comment_file=""

    while [[ $# -gt 0 ]]; do
        case "${1:-}" in
            --obsolete)
                obsolete_ids="${2:-}"
                shift 2
                ;;
            --comment-file)
                comment_file="${2:-}"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done

    [[ $# -lt 2 ]] && { echo "Error: missing PR number or file"; usage; }

    local pr="$1"
    local file="$2"
    local desc="${3:-$(basename "$file")}"
    local comment="${4:-}"
    local auto_cc="$AUTO_CC_DEFAULT"

    if [[ -n "$comment_file" && -n "$comment" ]]; then
        echo "Error: pass either inline comment text or --comment-file, not both." >&2
        exit 1
    fi

    if [[ ! -f "$file" ]]; then
        echo "Error: file not found: $file" >&2
        exit 1
    fi

    if [[ -n "$comment_file" ]]; then
        comment="$(read_text_file_or_die "$comment_file")"
    fi

    file="$(realpath "$file")"

    echo "Attaching '$file' to bug $pr..."
    echo ""
    echo "  Bug:     https://gcc.gnu.org/bugzilla/show_bug.cgi?id=$pr"
    echo "  File:    $file"
    echo "  Desc:    $desc"
    [[ -n "$comment" ]] && echo "  Comment: $comment"
    [[ -n "$obsolete_ids" ]] && echo "  Obsolete: $obsolete_ids"
    echo ""
    confirm_bugzilla_write "attach file to bug $pr"

    python3 - "$pr" "$file" "$desc" "$comment" "$auto_cc" "$obsolete_ids" <<'PYEOF'
import sys, bugzilla
pr, path, desc, comment, auto_cc, obsolete_ids = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
bz = bugzilla.Bugzilla("https://gcc.gnu.org/bugzilla/xmlrpc.cgi")
kwargs = dict(content_type="text/plain", is_patch=True)
if comment:
    kwargs["comment"] = comment
att_id = bz.attachfile(int(pr), path, desc, **kwargs)
if obsolete_ids:
    ids = [int(item) for item in obsolete_ids.split(",") if item]
    if ids:
        bz._backend.bug_attachment_update(ids, {"is_obsolete": True})
bz.update_bugs(int(pr), bz.build_update(cc_add=[email for email in auto_cc.split(",") if email]))
print(f"Attachment ID: {att_id}")
if obsolete_ids:
    print(f"Marked obsolete: {obsolete_ids}")
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
    confirm_bugzilla_write "update CC on bug $pr"

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
    comments)
        [[ $# -lt 2 ]] && { echo "Error: missing PR number"; usage; }
        cmd_comments "$2"
        ;;
    attachments)
        [[ $# -lt 2 ]] && { echo "Error: missing PR number"; usage; }
        cmd_attachments "$2"
        ;;
    download)
        [[ $# -lt 2 ]] && { echo "Error: missing PR number"; usage; }
        cmd_download "$2" "${3:-}"
        ;;
    search)
        [[ $# -lt 2 ]] && { echo "Error: missing search term"; usage; }
        cmd_search "$2"
        ;;
    regressions)
        cmd_regressions
        ;;
    new)
        [[ $# -lt 4 ]] && { echo "Error: missing component, summary, or comment file"; usage; }
        cmd_new "$2" "$3" "$4" "${5:-}"
        ;;
    comment)
        [[ $# -lt 3 ]] && { echo "Error: missing PR number or comment text"; usage; }
        cmd_comment "$2" "$3"
        ;;
    comment-file)
        [[ $# -lt 3 ]] && { echo "Error: missing PR number or comment file"; usage; }
        cmd_comment_file "$2" "$3"
        ;;
    reply)
        [[ $# -lt 4 ]] && { echo "Error: missing PR number, comment number, or reply text"; usage; }
        cmd_reply "$2" "$3" "$4"
        ;;
    reply-file)
        [[ $# -lt 4 ]] && { echo "Error: missing PR number, comment number, or reply file"; usage; }
        cmd_reply_file "$2" "$3" "$4"
        ;;
    attach)
        shift
        cmd_attach "$@"
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
