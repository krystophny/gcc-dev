#!/bin/bash
# gcc-send-patch.sh - Send a patch to gcc-patches@ mailing list
#
# Usage:
#   gcc-send-patch.sh <patch-file>           # Send with default to: gcc-patches@
#   gcc-send-patch.sh --dry-run <patch-file> # Preview without sending
#   gcc-send-patch.sh submit <pr> [branch] [--execute]  # Send generated packet
#
# Prerequisites:
#   git send-email must be configured in gcc/ with SMTP settings.
#   Run from the gcc-dev root directory.
#
# Requires: git-send-email, perl-io-socket-ssl, perl-authen-sasl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GCC_DIR="$SCRIPT_DIR/../gcc"

usage() {
    echo "Usage: $0 [--dry-run] <patch-file>"
    echo "   or: $0 submit <pr> [branch] [--execute]"
    echo ""
    echo "Sends a GCC patch to gcc-patches@gcc.gnu.org via git send-email."
    echo ""
    echo "Options:"
    echo "  --dry-run    Preview the email without sending"
    echo ""
    echo "Examples:"
    echo "  $0 pr/123280/0001-libgomp-Remove-contiguous.patch"
    echo "  $0 --dry-run pr/103276/0001-fortran-Skip-pointer.patch"
    echo "  $0 submit 120723 gcc-15 --execute"
    echo ""
    echo "The patch must be a git format-patch output file."
    exit 1
}

DRY_RUN=""
PATCH_FILE=""

if [[ "${1:-}" == "submit" ]]; then
    shift
    exec python3 "$(dirname "$0")/gcc-workflow.py" submit-mail "$@"
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            PATCH_FILE="$1"
            shift
            ;;
    esac
done

[[ -z "$PATCH_FILE" ]] && usage

if [[ ! -f "$PATCH_FILE" ]]; then
    echo "Error: patch file not found: $PATCH_FILE" >&2
    exit 1
fi

if [[ ! -d "$GCC_DIR/.git" ]]; then
    echo "Error: gcc/ directory not found. Run from gcc-dev root." >&2
    exit 1
fi

echo "=== Patch to send ==="
head -20 "$PATCH_FILE"
echo "..."
echo ""
echo "To: gcc-patches@gcc.gnu.org"
echo "File: $PATCH_FILE"
if [[ -n "$DRY_RUN" ]]; then
    echo "Mode: DRY RUN (no email will be sent)"
fi
echo ""

confirm="${GCC_SEND_PATCH_ASSUME_YES:-}"
if [[ -z "$confirm" ]]; then
    read -rp "Proceed? [y/N] " confirm
fi
if [[ "$confirm" != "1" && "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

git -C "$GCC_DIR" send-email \
    --to="gcc-patches@gcc.gnu.org" \
    --confirm=always \
    $DRY_RUN \
    "$(realpath "$PATCH_FILE")"

if [[ -n "$DRY_RUN" ]]; then
    echo ""
    echo "Dry run complete. No email was sent."
else
    echo ""
    echo "Patch sent successfully."
fi
