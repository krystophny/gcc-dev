#!/usr/bin/env python3
"""Rank GCC testsuite files by provenance and license-risk heuristics."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


TEST_ROOTS = (
    "gcc/gcc/testsuite",
    "gcc/libgomp/testsuite",
)

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
    ".c",
    ".cc",
    ".cp",
    ".cpp",
    ".cxx",
    ".c++",
    ".C",
    ".h",
    ".hh",
    ".hpp",
    ".H",
    ".f",
    ".f90",
    ".f95",
    ".f03",
    ".f08",
    ".for",
    ".fpp",
    ".go",
    ".py",
    ".sh",
    ".awk",
    ".exp",
    ".inc",
    ".def",
    ".json",
    ".sarif",
    ".rs",
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
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "license.txt",
    "COPYING",
    "COPYING3",
    "COPYRIGHT",
)

SOURCE_PATTERNS = (
    "gcc/testsuite/",
    "libgomp/testsuite/",
    "gfortran.dg/",
    "libgomp.",
    "../",
    "./",
)

ORIGIN_PATTERN = re.compile(
    r"\b(copied|adapted|derived|based)\b.{0,80}\b(from|on)\b", re.IGNORECASE
)
INTERNAL_SOURCE_PATTERN = re.compile(
    r"\b(copied|adapted|derived|based)\b.{0,120}"
    r"(?:gcc/testsuite/|libgomp/testsuite/|gfortran\.dg/|libgomp\.|'\.\.?/|\"\.\.?/|\.\./|\./)",
    re.IGNORECASE,
)
SPDX_PATTERN = re.compile(r"SPDX-(?:File|Snippet|License)", re.IGNORECASE)
GNU_PATTERN = re.compile(r"gnu\.org/licenses|Free Software Foundation", re.IGNORECASE)
COPYRIGHT_PATTERN = re.compile(
    r"copyright\s*(?:\([cC]\)|©)?\s*(?P<holder>.+)",
    re.IGNORECASE,
)
EXTERNAL_COPYRIGHT_MARKERS = (
    "The Go Authors",
    "LAPACK",
    "BLAS",
    "SARIF",
    "sollve_vv",
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
class Finding:
    path: str
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    nearby_license_files: list[str] = field(default_factory=list)
    header_excerpt: str = ""
    manifest: list[dict[str, object]] = field(default_factory=list)
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
            "manifest": self.manifest,
            "header_excerpt": self.header_excerpt,
            "suppressed": self.suppressed,
            "local_contribution": self.local_contribution,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rank GCC testsuite files by provenance and license-risk heuristics. "
            "Higher scores mean more likely missing or incomplete attribution."
        )
    )
    parser.add_argument(
        "--include-testsuites",
        action="store_true",
        help="Opt in to scanning GCC testsuite paths. By default they are excluded.",
    )
    parser.add_argument(
        "--scope",
        choices=("local", "all"),
        default="local",
        help=(
            "Scan only tests changed relative to upstream/master plus local worktree "
            "changes, or scan the whole inherited testsuite history."
        ),
    )
    parser.add_argument(
        "--manifest",
        default=".provenance/testsuites.toml",
        help="Optional TOML manifest with reviewed paths and risk adjustments.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Show the top N candidates in the text report.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=1,
        help="Only include findings with at least this score.",
    )
    parser.add_argument(
        "--json",
        help="Write the full report as JSON to this path.",
    )
    parser.add_argument(
        "--no-fail-on-findings",
        action="store_true",
        help="Exit with status 0 even when candidates are found.",
    )
    parser.add_argument(
        "--include-suppressed",
        action="store_true",
        help="Include reviewed false positives in the report output.",
    )
    return parser.parse_args()


def run_git_gcc(
    repo_root: Path, *args: str, check: bool = True, ignore_errors: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root / "gcc"), *args],
        check=check,
        capture_output=True,
        text=True,
        errors="replace",
    )


def git_ls_files(repo_root: Path) -> list[str]:
    try:
        result = run_git_gcc(repo_root, "ls-files", *GCC_TEST_ROOTS)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"failed to enumerate gcc testsuite files: {exc}") from exc
    files = [f"gcc/{line}" for line in result.stdout.splitlines() if line]
    return files


def git_grep_candidates(repo_root: Path, entries: Iterable[ManifestEntry]) -> list[str]:
    cmd = ["git", "-C", str(repo_root / "gcc"), "grep", "-I", "-l", "-E"]
    pattern = "|".join(re.escape(item) for item in CANDIDATE_GREP_PATTERNS)
    cmd.extend([pattern, "--", *GCC_TEST_ROOTS])
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"failed to grep gcc testsuite files: {exc}") from exc

    files = {f"gcc/{line}" for line in result.stdout.splitlines() if line}
    for entry in entries:
        if any(char in entry.path for char in "*?[]"):
            files.update(path for path in git_ls_files(repo_root) if fnmatch.fnmatch(path, entry.path))
        else:
            files.add(entry.path)
    return sorted(files)


def resolve_compare_ref(repo_root: Path) -> str | None:
    for ref in ("upstream/master", "origin/master"):
        result = run_git_gcc(repo_root, "rev-parse", "--verify", ref, check=False)
        if result.returncode == 0:
            return ref
    return None


def git_changed_tests(repo_root: Path) -> set[str]:
    files: set[str] = set()
    compare_ref = resolve_compare_ref(repo_root)
    commands: list[list[str]] = []
    if compare_ref:
        commands.append(["diff", "--name-only", f"{compare_ref}...HEAD", "--", *GCC_TEST_ROOTS])
    commands.extend(
        [
            ["diff", "--name-only", "--cached", "--", *GCC_TEST_ROOTS],
            ["diff", "--name-only", "--", *GCC_TEST_ROOTS],
            ["ls-files", "--others", "--exclude-standard", "--", *GCC_TEST_ROOTS],
        ]
    )
    for command in commands:
        result = run_git_gcc(repo_root, *command, check=False)
        if result.returncode != 0:
            continue
        files.update(f"gcc/{line}" for line in result.stdout.splitlines() if line)
    return files


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


def is_candidate(path: str) -> bool:
    name = os.path.basename(path)
    if name in SKIP_NAMES or name.startswith("ChangeLog"):
        return False
    if name in LICENSE_FILE_NAMES or name.endswith(".patch"):
        return False
    suffix = Path(path).suffix
    return suffix in TEXT_SUFFIXES or name.endswith(".exp")


def read_prefix(path: Path, lines: int = 80) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return "".join(handle.readline() for _ in range(lines))
    except OSError:
        return ""


def find_nearby_license_files(path: Path, repo_root: Path) -> list[str]:
    rel = path.relative_to(repo_root)
    search_dirs = [path.parent]
    for parent in path.parents:
        if parent == repo_root:
            break
        if parent not in search_dirs:
            search_dirs.append(parent)
        rel_parent = parent.relative_to(repo_root)
        if str(rel_parent) in TEST_ROOTS:
            break
    found = []
    for directory in search_dirs:
        for name in LICENSE_FILE_NAMES:
            candidate = directory / name
            if candidate.is_file():
                found.append(str(candidate.relative_to(repo_root)))
    return found


def manifest_matches(path: str, entries: Iterable[ManifestEntry]) -> list[ManifestEntry]:
    return [entry for entry in entries if fnmatch.fnmatch(path, entry.path)]


def append_manifest_record(finding: Finding, entry: ManifestEntry) -> None:
    finding.manifest.append(
        {
            "path": entry.path,
            "reviewed": entry.reviewed,
            "kind": entry.kind,
            "basis": entry.basis,
            "notes": entry.notes,
            "reviewed_on": entry.reviewed_on,
            "reviewed_by": entry.reviewed_by,
            "evidence": entry.evidence,
        }
    )


def analyze_file(
    repo_root: Path,
    path: str,
    manifest_entries: list[ManifestEntry],
    local_paths: set[str],
) -> Finding | None:
    full_path = repo_root / path
    prefix = read_prefix(full_path)
    if not prefix.strip():
        return None

    finding = Finding(path=path)
    finding.local_contribution = path in local_paths
    finding.header_excerpt = "\n".join(line.rstrip() for line in prefix.splitlines()[:8])
    finding.nearby_license_files = find_nearby_license_files(full_path, repo_root)

    lower_prefix = prefix.lower()
    has_spdx = bool(SPDX_PATTERN.search(prefix))
    has_gnu_header = bool(GNU_PATTERN.search(prefix))
    has_origin_phrase = bool(ORIGIN_PATTERN.search(prefix))
    has_internal_origin = bool(INTERNAL_SOURCE_PATTERN.search(prefix))

    matches = manifest_matches(path, manifest_entries)
    for entry in matches:
        append_manifest_record(finding, entry)
        if entry.reviewed:
            finding.add(-20, f"reviewed manifest entry matched: {entry.path}")
        if entry.kind == "false_positive":
            finding.suppressed = True
            finding.add(-1000, f"reviewed false positive: {entry.path}")
        elif entry.kind == "accepted_external":
            finding.add(-60, f"reviewed external content with acceptable attribution trail: {entry.path}")
        elif entry.kind == "project_policy":
            finding.suppressed = True
            finding.add(-1000, f"accepted by GCC testsuite project policy: {entry.path}")
        elif entry.kind == "needs_local_license":
            finding.add(15, f"reviewed external content still needs clearer local license placement: {entry.path}")
        if entry.risk_adjustment:
            finding.add(entry.risk_adjustment, f"manifest risk adjustment {entry.risk_adjustment:+d}: {entry.path}")

    if has_spdx:
        finding.add(-35, "SPDX provenance or license metadata present")
    if has_gnu_header:
        finding.add(-30, "GNU/FSF copyright or license header present")
    if finding.nearby_license_files:
        finding.add(-20, "nearby license file present")

    if has_origin_phrase:
        if has_internal_origin:
            finding.add(-35, "copy/adaptation points to an in-tree GCC source")
        else:
            finding.add(55, "copy/adaptation refers to an external or unclear origin")

    for marker, score in EXTERNAL_ORIGIN_MARKERS.items():
        if marker in lower_prefix:
            finding.add(score, f"external origin marker: {marker}")

    if "license that can be found in the license file" in lower_prefix and not finding.nearby_license_files:
        finding.add(35, "references a LICENSE file that is not present nearby")

    if "all rights reserved" in lower_prefix:
        finding.add(20, "contains all-rights-reserved language")

    if "bsd-style" in lower_prefix and not finding.nearby_license_files:
        finding.add(20, "mentions BSD-style licensing without nearby license text")

    if path.startswith("gcc/gcc/testsuite/go.test/"):
        finding.add(15, "imported go.test subtree")

    for match in COPYRIGHT_PATTERN.finditer(prefix):
        holder = match.group("holder").strip()
        if not holder:
            continue
        normalized = holder.lower()
        if "free software foundation" in normalized:
            continue
        if "gnu" in normalized and "org" in normalized:
            continue
        finding.add(70, f"non-FSF copyright holder: {holder}")
        break

    if not finding.nearby_license_files and any(marker.lower() in lower_prefix for marker in EXTERNAL_COPYRIGHT_MARKERS):
        finding.add(15, "external provenance appears without local license companion")

    if finding.local_contribution and finding.score > 0:
        finding.add(20, "locally added or modified test needs review as our contribution")

    if finding.suppressed:
        return finding
    if finding.score <= 0:
        return None
    return finding


def render_text(findings: list[Finding], top: int, suppressed_count: int) -> str:
    lines = []
    lines.append(f"ranked_candidates={len(findings)}")
    lines.append(f"suppressed_candidates={suppressed_count}")
    for index, finding in enumerate(findings[:top], start=1):
        reasons = "; ".join(finding.reasons[:4])
        if len(finding.reasons) > 4:
            reasons += "; ..."
        licenses = ", ".join(finding.nearby_license_files) if finding.nearby_license_files else "-"
        lines.append(
            f"{index:02d}. score={finding.score:3d} severity={finding.severity:8s} "
            f"path={finding.path}"
        )
        lines.append(f"    local_contribution: {'yes' if finding.local_contribution else 'no'}")
        lines.append(f"    reasons: {reasons}")
        lines.append(f"    nearby_licenses: {licenses}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    manifest_entries = load_manifest(repo_root / args.manifest)
    local_paths = git_changed_tests(repo_root)

    if not args.include_testsuites:
        report = {
            "repo_root": str(repo_root),
            "manifest": args.manifest if manifest_entries else None,
            "scope": args.scope,
            "include_testsuites": False,
            "local_candidate_count": 0,
            "candidate_count": 0,
            "suppressed_count": 0,
            "top": [],
            "findings": [],
        }
        if args.json:
            output_path = Path(args.json)
            output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("ranked_candidates=0")
        print("suppressed_candidates=0")
        print("testsuite_scan=disabled (pass --include-testsuites to opt in)")
        return 0

    findings = []
    if args.scope == "local":
        candidate_paths = sorted(local_paths)
    else:
        candidate_paths = git_grep_candidates(repo_root, manifest_entries)

    for path in candidate_paths:
        if not is_candidate(path):
            continue
        finding = analyze_file(repo_root, path, manifest_entries, local_paths)
        if finding and (finding.suppressed or finding.score >= args.min_score):
            findings.append(finding)

    suppressed_count = sum(1 for finding in findings if finding.suppressed)
    if not args.include_suppressed:
        findings = [finding for finding in findings if not finding.suppressed]

    findings.sort(key=lambda item: (-item.score, item.path))

    report = {
        "repo_root": str(repo_root),
        "manifest": args.manifest if manifest_entries else None,
        "scope": args.scope,
        "include_testsuites": True,
        "local_candidate_count": len(local_paths),
        "candidate_count": len(findings),
        "suppressed_count": suppressed_count,
        "top": [finding.to_json() for finding in findings[: args.top]],
        "findings": [finding.to_json() for finding in findings],
    }

    if args.json:
        output_path = Path(args.json)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(render_text(findings, args.top, suppressed_count))
    if findings and not args.no_fail_on_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
