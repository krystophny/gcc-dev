"""Shared primitives for provenance scanners.

Extracted from scripts/check_testsuite_provenance.py so both the legacy
testsuite scanner and the new non-testsuite source scanner can reuse the
same tokeniser, regex heuristics, and config loaders without duplicating
them.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - python < 3.11
    tomllib = None


GCC_TEST_ROOTS = (
    "gcc/testsuite",
    "libgomp/testsuite",
)

CANDIDATE_GREP_PATTERNS = (
    "Copied from",
    "copied from",
    "Adapted from",
    "adapted from",
    "Derived from",
    "derived from",
    "Based on",
    "based on",
    "SPDX-",
    "Copyright",
    "copyright",
    "license",
    "License",
    "The Go Authors",
    "OpenMP",
    "OpenACC",
    "LAPACK",
    "BLAS",
    "SARIF",
    "sollve_vv",
)

TEXT_SUFFIXES = {
    ".c", ".cc", ".cp", ".cpp", ".cxx", ".c++", ".C",
    ".h", ".hh", ".hpp", ".H",
    ".f", ".f90", ".f95", ".f03", ".f08", ".for", ".fpp",
    ".go", ".py", ".sh", ".awk", ".exp", ".inc", ".def",
    ".json", ".sarif", ".rs",
    ".d", ".di", ".m", ".mm",
    ".tcc", ".ipp",
    ".S", ".s",
}

SKIP_NAMES = {
    "ChangeLog",
    "README",
    "README.compat",
    "README.libquadmath",
    "README.gcc",
    "README.gnat",
}

LICENSE_FILE_NAMES = (
    "LICENSE", "LICENSE.txt", "LICENSE.md", "license.txt",
    "COPYING", "COPYING3", "COPYRIGHT",
)

ORIGIN_PATTERN = re.compile(
    r"\b(copied|adapted|derived|based)\b.{0,80}\b(from|on)\b", re.IGNORECASE
)
# GNU-project convention used across glibc, gnulib, gettext, and the
# embedded copies GCC ships.  A file that says "the canonical source of
# this file is maintained with the GNU C Library" (or the GNU gettext
# runtime, gnulib, ...) is explicitly attributing its upstream even
# though it avoids the copied/derived/adapted phrasing.
CANONICAL_SOURCE_PATTERN = re.compile(
    r"canonical\s+source\s+of\s+this\s+file\s+is\s+maintained\s+with\b",
    re.IGNORECASE,
)
INTERNAL_SOURCE_PATTERN = re.compile(
    r"\b(copied|adapted|derived|based)\b.{0,120}"
    r"(?:gcc/testsuite/|libgomp/testsuite/|gfortran\.dg/|libgomp\.|'\.\.?/|\"\.\.?/|\.\./|\./)",
    re.IGNORECASE,
)
SPDX_PATTERN = re.compile(r"SPDX-(?:File|Snippet|License)", re.IGNORECASE)
GNU_PATTERN = re.compile(r"gnu\.org/licenses|Free Software Foundation", re.IGNORECASE)
COPYRIGHT_PATTERN = re.compile(
    r"copyright\s*(?:\([cC]\)|\u00a9)?\s*(?P<holder>.+)",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://|\bgit://|\bgit@", re.IGNORECASE)
EXTERNAL_COPYRIGHT_MARKERS = (
    "The Go Authors", "LAPACK", "BLAS", "SARIF", "sollve_vv",
)
EXTERNAL_ORIGIN_MARKERS = {
    "go authors": 85,
    "lapack": 55,
    "blas": 50,
    "sollve_vv": 45,
    "sarif": 35,
    "json example": 30,
    "specification": 25,
    "example document": 30,
}
INLINE_EXTERNAL_LICENSE_MARKERS = (
    "redistribution and use in source and binary forms",
    "permission to use, copy, modify, and distribute this",
    "this software is provided 'as-is'",
    'this software is provided "as is"',
    "see copyright notice in",
)

PART_OF_PATTERN = re.compile(
    r"part of the\s+([^\n\r,.;]+?)\s+(library|project|compiler|runtime|suite)",
    re.IGNORECASE,
)

TOKEN_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z_0-9]*|\d+|==|!=|<=|>=|->|::|&&|\|\||[-+*/%<>&|^~!?=(){}\[\],.;:]"
)


@dataclass
class ManifestEntry:
    path: str
    reviewed: bool = False
    kind: str = ""
    basis: str = ""
    risk_adjustment: int = 0
    notes: str = ""
    reviewed_on: str = ""
    reviewed_by: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass
class CorpusEntry:
    path: str = ""
    path_prefix: str = ""
    source_name: str = ""
    url: str = ""
    url_prefix: str = ""
    origin_class: str = ""
    notes: str = ""


@dataclass
class Finding:
    path: str
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    nearby_license_files: list[str] = field(default_factory=list)
    source_tree_license_files: list[str] = field(default_factory=list)
    header_excerpt: str = ""
    manifest: list[dict[str, object]] = field(default_factory=list)
    corpus_matches: list[dict[str, object]] = field(default_factory=list)
    online_matches: list[dict[str, object]] = field(default_factory=list)
    suppressed: bool = False
    local_contribution: bool = False

    @property
    def severity(self) -> str:
        if self.score >= 100:
            return "critical"
        if self.score >= 70:
            return "high"
        if self.score >= 40:
            return "medium"
        return "low"

    def add(self, score: int, reason: str) -> None:
        self.score += score
        self.reasons.append(reason)

    def to_json(self) -> dict[str, object]:
        return {
            "path": self.path,
            "score": self.score,
            "severity": self.severity,
            "reasons": self.reasons,
            "nearby_license_files": self.nearby_license_files,
            "source_tree_license_files": self.source_tree_license_files,
            "manifest": self.manifest,
            "corpus_matches": self.corpus_matches,
            "online_matches": self.online_matches,
            "header_excerpt": self.header_excerpt,
            "suppressed": self.suppressed,
            "local_contribution": self.local_contribution,
        }


def tokenize_for_similarity(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def token_shingles(tokens: list[str], width: int = 5) -> set[tuple[str, ...]]:
    if len(tokens) < width:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def shingle_similarity(lhs: str, rhs: str) -> float:
    lhs_shingles = token_shingles(tokenize_for_similarity(lhs))
    rhs_shingles = token_shingles(tokenize_for_similarity(rhs))
    if not lhs_shingles or not rhs_shingles:
        return 0.0
    intersection = len(lhs_shingles & rhs_shingles)
    union = len(lhs_shingles | rhs_shingles)
    return intersection / union if union else 0.0


def line_similarity(lhs: str, rhs: str) -> float:
    lhs_lines = {line.strip() for line in lhs.splitlines() if line.strip()}
    rhs_lines = {line.strip() for line in rhs.splitlines() if line.strip()}
    if not lhs_lines or not rhs_lines:
        return 0.0
    intersection = len(lhs_lines & rhs_lines)
    union = len(lhs_lines | rhs_lines)
    return intersection / union if union else 0.0


def load_manifest(path: Path) -> list[ManifestEntry]:
    if not path.exists():
        return []
    if tomllib is None:
        raise SystemExit("tomllib is unavailable; cannot read manifest")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    entries = []
    for raw in data.get("entry", []):
        if "path" not in raw:
            continue
        entries.append(
            ManifestEntry(
                path=raw["path"],
                reviewed=bool(raw.get("reviewed", False)),
                kind=str(raw.get("kind", "")),
                basis=str(raw.get("basis", "")),
                risk_adjustment=int(raw.get("risk_adjustment", 0)),
                notes=str(raw.get("notes", "")),
                reviewed_on=str(raw.get("reviewed_on", "")),
                reviewed_by=str(raw.get("reviewed_by", "")),
                evidence=[str(item) for item in raw.get("evidence", [])],
            )
        )
    return entries


def load_corpus(path: Path) -> list[CorpusEntry]:
    if not path.exists():
        return []
    if tomllib is None:
        raise SystemExit("tomllib is unavailable; cannot read corpus config")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    entries: list[CorpusEntry] = []
    for raw in data.get("entry", []):
        if "path" not in raw or "url" not in raw:
            continue
        entries.append(
            CorpusEntry(
                path=str(raw["path"]),
                source_name=str(raw.get("source_name", raw["url"])),
                url=str(raw["url"]),
                origin_class=str(raw.get("origin_class", "")),
                notes=str(raw.get("notes", "")),
            )
        )
    for raw in data.get("tree", []):
        if "path_prefix" not in raw or "url_prefix" not in raw:
            continue
        entries.append(
            CorpusEntry(
                path_prefix=str(raw["path_prefix"]),
                source_name=str(raw.get("source_name", raw["url_prefix"])),
                url_prefix=str(raw["url_prefix"]),
                origin_class=str(raw.get("origin_class", "")),
                notes=str(raw.get("notes", "")),
            )
        )
    return entries


def corpus_matches_for_path(path: str, entries: Iterable[CorpusEntry]) -> list[CorpusEntry]:
    matches: list[CorpusEntry] = []
    for entry in entries:
        if entry.path and fnmatch.fnmatch(path, entry.path):
            matches.append(entry)
            continue
        if entry.path_prefix and path.startswith(entry.path_prefix):
            relative = path[len(entry.path_prefix) :].lstrip("/")
            matches.append(
                CorpusEntry(
                    path=path,
                    path_prefix=entry.path_prefix,
                    source_name=(
                        f"{entry.source_name.rstrip('/')}/{relative}" if relative else entry.source_name
                    ),
                    url=f"{entry.url_prefix.rstrip('/')}/{relative}" if relative else entry.url_prefix,
                    url_prefix=entry.url_prefix,
                    origin_class=entry.origin_class,
                    notes=entry.notes,
                )
            )
    return matches


def read_prefix(path: Path, lines: int = 80) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return "".join(handle.readline() for _ in range(lines))
    except OSError:
        return ""


def find_nearby_license_files(path: Path, repo_root: Path) -> list[str]:
    rel = path.relative_to(repo_root)
    search_dirs: list[Path] = [path.parent]
    for parent in path.parents:
        if parent == repo_root:
            break
        if parent not in search_dirs:
            search_dirs.append(parent)
    found: list[str] = []
    for directory in search_dirs:
        for name in LICENSE_FILE_NAMES:
            candidate = directory / name
            if candidate.is_file():
                found.append(str(candidate.relative_to(repo_root)))
    return found


def cached_fetch(url: str, cache_root: Path) -> str | None:
    cache_root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    target = cache_root / f"{digest}.txt"
    if not target.exists():
        request = urllib.request.Request(
            url, headers={"user-agent": "Mozilla/5.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                target.write_bytes(response.read())
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
    try:
        return target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def run_git(repo: Path, *args: str, check: bool = True):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
        errors="replace",
    )


def header_has_provenance_markers(prefix: str) -> tuple[bool, list[str]]:
    """Classify a file header as 'marked' or 'silent'.

    Returns (has_marker, evidence_list). A file is 'silent' when no provenance
    marker is found: plain Copyright ... FSF / Copyright ... GNU / blank header.
    Silent + high code-similarity is the dangerous class we hunt.
    """
    hits: list[str] = []
    if SPDX_PATTERN.search(prefix):
        hits.append("SPDX")
    if ORIGIN_PATTERN.search(prefix):
        hits.append("origin-phrase")
    if CANONICAL_SOURCE_PATTERN.search(prefix):
        hits.append("canonical-source")
    # Only treat a URL as a marker when it points somewhere other than GNU /
    # FSF. A bare `http://www.gnu.org/licenses/` is license boilerplate, not
    # an external provenance pointer.
    for url_match in URL_PATTERN.finditer(prefix):
        start = url_match.start()
        tail = prefix[start:start + 80].lower()
        if any(term in tail for term in ("gnu.org/licenses", "www.gnu.org", "fsf.org", "gcc.gnu.org")):
            continue
        hits.append("external-url")
        break
    lower = prefix.lower()
    for marker in INLINE_EXTERNAL_LICENSE_MARKERS:
        if marker in lower:
            hits.append(f"inline-license:{marker[:24]}")
            break
    for marker in EXTERNAL_COPYRIGHT_MARKERS:
        if marker.lower() in lower:
            hits.append(f"external-marker:{marker}")
            break
    for match in COPYRIGHT_PATTERN.finditer(prefix):
        holder = match.group("holder").strip()
        if not holder:
            continue
        normalized = holder.lower()
        if "free software foundation" in normalized:
            continue
        if "gnu" in normalized and "org" in normalized:
            continue
        hits.append(f"copyright:{holder[:40]}")
        break
    # "This file is part of the GNU MP Library" and similar origin statements.
    part_of = PART_OF_PATTERN.search(prefix)
    if part_of:
        project = part_of.group(1).strip()
        # Distinguish the hosting project (gcc/libiberty/libstdc++) from the
        # source project. If "gcc" or "libiberty" etc. appears we treat that
        # as host, not an external origin.
        lower_proj = project.lower()
        host_terms = (
            "gcc", "libiberty", "libquadmath", "libstdc++", "libgomp",
            "libgfortran", "libobjc", "libbacktrace", "libcpp", "libgrust",
            "libsanitizer", "gnu compiler collection",
        )
        if not any(host in lower_proj for host in host_terms):
            hits.append(f"part-of:{project[:48]}")
    return (bool(hits), hits)


def is_text_candidate(path: str) -> bool:
    name = os.path.basename(path)
    if name in SKIP_NAMES or name.startswith("ChangeLog"):
        return False
    if name in LICENSE_FILE_NAMES or name.endswith(".patch"):
        return False
    suffix = Path(path).suffix
    return suffix in TEXT_SUFFIXES or name.endswith(".exp")
