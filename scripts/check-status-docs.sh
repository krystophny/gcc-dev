#!/usr/bin/env bash
# Fail if a tracked .md outside the declared sources of truth contains
# status-shaped content. CLAUDE.md "Patch status — sources of truth"
# declares pr/<n>/status.json + pr/<n>/README.md + pr/backport-matrix.{md,json}
# + docs/upstream-master-commits.md as the only places that mirror PR state.
#
# Anything else with strings like "RESOLVED FIXED", "merged on trunk",
# "BZ still", "Patch on Bugzilla", or raw "attachment-NNN" filenames is
# almost certainly drift. Catches files like the deleted
# pr/regression-status.md / pr/bugzilla-review-pending.md the moment they
# reappear.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Allowlist: paths that are themselves a declared source of truth, and
# template/policy docs whose body legitimately discusses these patterns.
allowlist=(
    'pr/[0-9]*/README.md'
    'pr/[0-9]*/status.json'
    'pr/[0-9]*/submission/.*'
    'pr/[0-9]*/dumps/.*'
    'pr/[0-9]*/verification/.*'
    'pr/backport-matrix.md'
    'pr/backport-matrix.json'
    'pr/schema.json'
    'docs/upstream-master-commits.md'
    'docs/patch-workflow.md'
    'docs/upstream-submission.md'
    'docs/provenance-research.md'
    'docs/build-and-test.md'
    'docs/bug-patterns.md'
    'CLAUDE.md'
    'AGENTS.md'
    'GEMINI.md'
    'README.md'
    'DISCLAIMER.md'
    'LICENSE'
    '.claude/.*'
)

allowlist_re="$(IFS='|'; echo "^(${allowlist[*]})\$")"

pattern='RESOLVED FIXED|merged on trunk; BZ|BZ still `NEW`|Patch on Bugzilla|attachment-[0-9]{3,}'

mapfile -t hits < <(
    git ls-files '*.md' '*.txt' \
        | grep -Ev "$allowlist_re" \
        | xargs -r grep -lE "$pattern" 2>/dev/null
)

if [[ ${#hits[@]} -gt 0 ]]; then
    echo "error: tracked file(s) outside the declared sources of truth carry"
    echo "       status-shaped content. Either fold the data into pr/<n>/status.json"
    echo "       (write it via 'gcc-workflow.py sync-metadata') or delete the file."
    printf '  %s\n' "${hits[@]}"
    exit 1
fi

echo "check-status-docs: clean"
