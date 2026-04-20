#!/bin/bash
# Clone upstream source corpora listed in .provenance/corpus-sources.toml
# into corpusbin/src/<name>/ using economic sparse + blobless checkouts.
#
# Usage:
#   scripts/provenance/fetch_corpus.sh                   # fetch/update all
#   scripts/provenance/fetch_corpus.sh name1 name2 ...   # fetch selected
#   scripts/provenance/fetch_corpus.sh --prune-only      # just re-prune
#
# Post-checkout each clone is pruned to source-code file types so the
# fingerprint index does not waste work on manpages, markdown, assets.

set -eo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST="${ROOT}/.provenance/corpus-sources.toml"
CORPUS_ROOT="${ROOT}/corpusbin/src"

if [[ ! -f "${MANIFEST}" ]]; then
    echo "manifest not found: ${MANIFEST}" >&2
    exit 1
fi

mkdir -p "${CORPUS_ROOT}"

KEEP_REGEX='\.(c|cc|cpp|cxx|c\+\+|C|h|hh|hpp|hxx|H|inc|ipp|tcc|rs|go|d|di|m|mm|py|f|f90|f95|f03|f08|for|fpp|F|F90|S|s|asm)$'

log() { printf '[fetch_corpus] %s\n' "$*"; }

parse_manifest() {
    python3 - "${MANIFEST}" <<'PY'
import sys, tomllib, json
path = sys.argv[1]
with open(path, 'rb') as handle:
    data = tomllib.load(handle)
for entry in data.get('source', []):
    print(json.dumps({
        'name': entry['name'],
        'url': entry['url'],
        'branch': entry.get('branch', 'HEAD'),
        'origin_class': entry.get('origin_class', ''),
        'sparse_paths': entry.get('sparse_paths', []),
    }))
PY
}

rename_extensionless_headers() {
    # STL-style headers (microsoft/GSL, libstdc++ include/, parts of zig/std)
    # ship extensionless files.  Rename them to *.hpp before prune so they
    # survive KEEP_REGEX and is_text_candidate().  Only files under a path
    # segment named include or inc are renamed; top-level LICENSE/COPYING/
    # README/NEWS/AUTHORS and Makefiles are left alone.
    local dest="$1"
    find "${dest}" \
        -type f \
        \( -path "*/include/*" -o -path "*/inc/*" \) \
        -not -path "${dest}/.git/*" \
        -not -name .corpus-sha \
        -not -name '*.*' \
        -not -iname 'LICENSE*' \
        -not -iname 'COPYING*' \
        -not -iname 'COPYRIGHT*' \
        -not -iname 'README*' \
        -not -iname 'AUTHORS*' \
        -not -iname 'NEWS*' \
        -not -iname 'Makefile*' \
        -not -iname '*.in' \
        -exec sh -c '
            for f in "$@"; do
                if head -c 4096 "$f" 2>/dev/null | grep -qE "^\s*(#|//|/\*|namespace|template|class|struct|inline|constexpr|typedef|using|enum)" 2>/dev/null; then
                    mv "$f" "$f.hpp"
                fi
            done
        ' _ {} + 2>/dev/null || true
}

prune_clone() {
    local dest="$1"
    rename_extensionless_headers "${dest}"
    # remove anything not matching source-code extensions; then drop empty dirs.
    find "${dest}" \
        -regextype posix-extended \
        -type f \
        -not -path "${dest}/.git/*" \
        -not -name .corpus-sha \
        ! -iregex ".*${KEEP_REGEX}" \
        -delete 2>/dev/null || true
    find "${dest}" -type d -empty -not -path "${dest}/.git*" -delete 2>/dev/null || true
}

fetch_one() {
    local name="$1" url="$2" branch="$3" origin_class="$4"
    shift 4
    local sparse_paths=("$@")

    local dest="${CORPUS_ROOT}/${name}"

    if [[ -d "${dest}/.git" ]]; then
        log "update ${name} (${url}@${branch})"
        (
            cd "${dest}" || exit 1
            git sparse-checkout init --no-cone 2>/dev/null || true
            git sparse-checkout set --skip-checks -- "${sparse_paths[@]}" 2>/dev/null || \
                git sparse-checkout set -- "${sparse_paths[@]}" 2>/dev/null || true
            timeout 600 git fetch --depth=1 --filter=blob:none origin "${branch}"
            git checkout FETCH_HEAD
            git rev-parse FETCH_HEAD > .corpus-sha
        ) || { log "FAILED update ${name}"; return 1; }
    else
        log "clone ${name} (${url}@${branch}) sparse=${#sparse_paths[@]}"
        rm -rf "${dest}"
        if ! timeout 600 git clone \
            --no-checkout \
            --filter=blob:none \
            --depth=1 \
            --branch "${branch}" \
            --single-branch \
            "${url}" "${dest}"; then
            log "FAILED clone ${name} (${url}@${branch})"
            rm -rf "${dest}"
            return 1
        fi
        if [[ ! -d "${dest}/.git" ]]; then
            log "FAILED clone ${name}: ${dest} missing after git clone"
            return 1
        fi
        (
            cd "${dest}" || exit 1
            git sparse-checkout init --no-cone
            git sparse-checkout set --skip-checks -- "${sparse_paths[@]}" 2>/dev/null || \
                git sparse-checkout set -- "${sparse_paths[@]}"
            git checkout
            git rev-parse HEAD > .corpus-sha
        ) || { log "FAILED sparse-checkout ${name}"; return 1; }
    fi

    prune_clone "${dest}"
    local kept
    kept=$(find "${dest}" -type f -not -path "${dest}/.git/*" -not -name .corpus-sha | wc -l)
    local sha
    sha=$(cat "${dest}/.corpus-sha" 2>/dev/null || echo "?")
    log "done ${name} sha=${sha} files=${kept}"
}

PRUNE_ONLY=0
if [[ "${1:-}" == "--prune-only" ]]; then
    PRUNE_ONLY=1
    shift
fi

SELECT=("$@")
selected() {
    local name="$1"
    if [[ ${#SELECT[@]} -eq 0 ]]; then return 0; fi
    local want
    for want in "${SELECT[@]}"; do
        [[ "${want}" == "${name}" ]] && return 0
    done
    return 1
}

while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    name=$(echo "${line}" | jq -r '.name')
    url=$(echo "${line}" | jq -r '.url')
    branch=$(echo "${line}" | jq -r '.branch')
    origin=$(echo "${line}" | jq -r '.origin_class')
    mapfile -t sparse < <(echo "${line}" | jq -r '.sparse_paths[]')

    if ! selected "${name}"; then
        continue
    fi

    if [[ "${PRUNE_ONLY}" -eq 1 ]]; then
        if [[ -d "${CORPUS_ROOT}/${name}" ]]; then
            prune_clone "${CORPUS_ROOT}/${name}"
            log "pruned ${name}"
        fi
        continue
    fi

    if ! fetch_one "${name}" "${url}" "${branch}" "${origin}" "${sparse[@]}"; then
        log "FAILED ${name}"
    fi
done < <(parse_manifest)

log "corpus root: ${CORPUS_ROOT}"
du -sh "${CORPUS_ROOT}" 2>/dev/null || true
