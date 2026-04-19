#!/usr/bin/env python3
"""Silent-imports scanner for non-testsuite GCC source.

Strategy:
  1. Enumerate all non-testsuite GCC source per .provenance/source-scope.toml.
  2. Classify each header as 'silent' (no SPDX / non-FSF copyright / URL /
     origin phrase / inline external license) or 'marked'.
  3. Fingerprint the file (winnowing k=8 w=5, MinHash num_perm=128).
  4. Probe the corpus LSH index for top-K candidate source matches.
  5. For each hit: compute winnow density, longest run, token Jaccard,
     line Jaccard. Optionally run PMD CPD as an independent cross-check.
  6. Risk-score with highest weight given to silent files with strong
     matches. Emit JSON + text, sorted by severity.

Silent header + high code match = an adapted or copied file sitting in
GCC source without any attribution — the dangerous class this tool hunts.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import pickle
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import tlsh

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.provenance._lib import (  # noqa: E402
    header_has_provenance_markers,
    is_text_candidate,
    line_similarity,
    read_prefix,
    shingle_similarity,
    tokenize_for_similarity,
)
from scripts.provenance.fingerprint import (  # noqa: E402
    DEFAULT_K,
    DEFAULT_MINHASH_PERM,
    DEFAULT_WINDOW,
    fingerprint_text,
    longest_run,
    minhash_from_bytes,
    winnow_density,
)

SCOPE_PATH = REPO_ROOT / ".provenance" / "source-scope.toml"
INDEX_DB = REPO_ROOT / "corpusbin" / "index" / "corpus.sqlite"
LSH_PKL = REPO_ROOT / "corpusbin" / "index" / "corpus.lsh.pkl"
CORPUS_ROOT = REPO_ROOT / "corpusbin" / "src"
CPD_DIR = REPO_ROOT / "corpusbin" / "reports" / "cpd"

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


@dataclass
class Match:
    project: str
    relpath: str
    tokens: int
    winnow_density: float
    matched_winnows: int
    longest_run: int
    shingle_jaccard: float
    line_jaccard: float
    tlsh_distance: int
    cpd_clusters: int = 0
    cpd_longest: int = 0


@dataclass
class SourceFinding:
    path: str
    header_class: str
    header_evidence: list[str]
    bytes: int
    tokens: int
    severity: str = "low"
    score: float = 0.0
    matches: list[Match] = field(default_factory=list)
    header_excerpt: str = ""


def load_scope() -> tuple[list[str], list[tuple[str, str]]]:
    if not SCOPE_PATH.exists() or tomllib is None:
        return ([], [])
    with SCOPE_PATH.open("rb") as handle:
        data = tomllib.load(handle)
    includes = [entry["path_prefix"] for entry in data.get("include", []) if "path_prefix" in entry]
    excludes = [(entry["path"], entry.get("reason", ""))
                for entry in data.get("exclude", []) if "path" in entry]
    return includes, excludes


def in_scope(path: str, includes: list[str], excludes: list[tuple[str, str]]) -> bool:
    if includes and not any(path.startswith(prefix) for prefix in includes):
        return False
    for pattern, _reason in excludes:
        if fnmatch.fnmatch(path, pattern):
            return False
    return True


def git_ls_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files"],
        capture_output=True, text=True, check=True,
    )
    return [f"gcc/{line}" for line in result.stdout.splitlines() if line]


def unpack_hashes(blob: bytes) -> list[int]:
    return [int.from_bytes(blob[i:i + 8], "little", signed=True) for i in range(0, len(blob), 8)]


def classify(header_silent: bool, best: Match | None) -> tuple[str, float]:
    if best is None:
        return ("low", 0.0)
    density = best.winnow_density
    shingle = best.shingle_jaccard
    run = best.longest_run
    line = best.line_jaccard
    score = 100.0 * density + 60.0 * shingle + 0.25 * run
    # A silent high-severity finding must have at least *some* verbatim
    # line overlap. Without it, the hit is a winnow k-gram collision
    # against a large data-table upstream (Unicode property tables etc.),
    # not an actual adaptation. Cap such cases at medium.
    LINE_FLOOR_HIGH = 0.06
    if header_silent and line < LINE_FLOOR_HIGH:
        if density >= 0.25 and shingle >= 0.20:
            return ("medium", score * 0.6)
        return ("low", score * 0.3)
    if not header_silent:
        # Marked file: high match just means we should double-check the trail,
        # not that it's an unattributed import.
        if density >= 0.85 or shingle >= 0.85:
            return ("review", score)
        if density >= 0.60 or shingle >= 0.70:
            return ("review", score * 0.8)
        return ("low", score * 0.5)
    # silent header with non-trivial line overlap
    # Require both token Jaccard and winnow density to be meaningful so that
    # a single-metric outlier (e.g. Python vs .awk sharing common k-grams)
    # does not trigger a false positive.
    strong = density >= 0.60 and shingle >= 0.45
    partial = density >= 0.35 and shingle >= 0.30
    weak = density >= 0.25 and shingle >= 0.20
    if strong or shingle >= 0.70:
        return ("critical", score + 50)
    if partial or shingle >= 0.45:
        return ("high", score + 20)
    if weak or shingle >= 0.30:
        return ("medium", score)
    return ("low", score)


def run_cpd(candidate: Path, corpus_file: Path) -> tuple[int, int]:
    try:
        CPD_DIR.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "pmd", "cpd",
                "--minimum-tokens", "50",
                "--language", guess_cpd_language(candidate, corpus_file),
                "--format", "csv",
                "--no-fail-on-violation",
                "--skip-lexical-errors",
                str(candidate),
                str(corpus_file),
            ],
            capture_output=True, text=True, timeout=60,
        )
        csv = result.stdout.strip().splitlines()
        if len(csv) <= 1:
            return (0, 0)
        clusters = len(csv) - 1
        # each line: lines,tokens,occurrences,file1,start1,... — take max "lines" field
        best = 0
        for row in csv[1:]:
            try:
                best = max(best, int(row.split(",", 1)[0]))
            except (ValueError, IndexError):
                continue
        return (clusters, best)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return (0, 0)


def guess_cpd_language(a: Path, b: Path) -> str:
    # PMD CPD does not ship a standalone "c" grammar — cpp handles C too.
    exts = {p.suffix.lower() for p in (a, b)}
    if exts & {".rs"}:
        return "rust"
    if exts & {".go"}:
        return "go"
    if exts & {".py"}:
        return "python"
    if exts & {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".fpp"}:
        return "fortran"
    return "cpp"


def analyze_candidate(
    conn: sqlite3.Connection,
    lsh,
    candidate_path: Path,
    rel_path: str,
    top_k: int,
    run_cpd_for: int,
    cpd_rank: int,
) -> SourceFinding | None:
    try:
        data = candidate_path.read_bytes()
    except OSError:
        return None
    if len(data) < 256:
        return None
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return None
    fp = fingerprint_text(text, k=DEFAULT_K, window=DEFAULT_WINDOW, num_perm=DEFAULT_MINHASH_PERM)
    if fp.token_count < 80:
        return None

    prefix = read_prefix(candidate_path, lines=80)
    has_marker, evidence = header_has_provenance_markers(prefix)

    finding = SourceFinding(
        path=rel_path,
        header_class="marked" if has_marker else "silent",
        header_evidence=evidence,
        bytes=len(data),
        tokens=fp.token_count,
        header_excerpt="\n".join(line.rstrip() for line in prefix.splitlines()[:8]),
    )

    try:
        cand_mh = minhash_from_bytes(fp.minhash_bytes)
    except ValueError:
        return finding

    hits = lsh.query(cand_mh)
    if not hits:
        # fall back: single TLSH probe is not useful without the LSH hit set
        return finding

    try:
        cand_tlsh = tlsh.hash(data)
    except Exception:
        cand_tlsh = ""

    # Score each hit with full precision.
    cur = conn.cursor()
    scored: list[tuple[float, Match, Path]] = []
    for hit_id in hits[: max(top_k * 2, 10)]:
        row = cur.execute(
            "SELECT project, relpath, tokens, tlsh, winnow_hashes FROM files WHERE id=?",
            (int(hit_id),),
        ).fetchone()
        if row is None:
            continue
        project, relpath, corp_tokens, corp_tlsh, corp_fp_blob = row
        corp_fps = unpack_hashes(corp_fp_blob)
        matched, density = winnow_density(fp.winnow_hashes, corp_fps)
        if matched == 0:
            continue
        corp_path = CORPUS_ROOT / project / relpath
        if not corp_path.exists():
            continue
        try:
            corp_text = corp_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        shingle_j = shingle_similarity(text, corp_text)
        line_j = line_similarity(text, corp_text)
        corp_positions = list(range(len(corp_fps)))
        run = longest_run(fp.winnow_positions, corp_positions, fp.winnow_hashes, corp_fps)
        try:
            dist = tlsh.diff(cand_tlsh, corp_tlsh) if cand_tlsh and corp_tlsh else -1
        except Exception:
            dist = -1
        match = Match(
            project=project,
            relpath=relpath,
            tokens=corp_tokens,
            winnow_density=round(density, 4),
            matched_winnows=matched,
            longest_run=run,
            shingle_jaccard=round(shingle_j, 4),
            line_jaccard=round(line_j, 4),
            tlsh_distance=dist,
        )
        rank = density + shingle_j + (run / 200.0)
        scored.append((rank, match, corp_path))

    scored.sort(key=lambda item: -item[0])
    finding.matches = [item[1] for item in scored[:top_k]]

    # CPD cross-check for top N matches.
    if run_cpd_for > 0:
        for rank_pos, (_rank, match, corp_path) in enumerate(scored[:cpd_rank]):
            clusters, longest = run_cpd(candidate_path, corp_path)
            match.cpd_clusters = clusters
            match.cpd_longest = longest

    if finding.matches:
        best = finding.matches[0]
        severity, score = classify(not has_marker, best)
        finding.severity = severity
        finding.score = round(score, 2)
    return finding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=3,
                        help="Top K corpus matches kept per candidate.")
    parser.add_argument("--cpd", type=int, default=0,
                        help="Run PMD CPD on the top N candidate/hit pairs.")
    parser.add_argument("--require-silent", action="store_true",
                        help="Only report findings where the header is silent.")
    parser.add_argument("--min-severity", choices=("low", "medium", "high", "critical", "review"),
                        default="medium")
    parser.add_argument("--json", help="Write full JSON report to this path.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after N candidates (smoke tests).")
    parser.add_argument("--only", action="append", default=[],
                        help="Restrict to paths matching this glob; can be repeated.")
    parser.add_argument("--include-excluded", action="store_true",
                        help="Ignore the source-scope.toml exclude list (diagnostic).")
    args = parser.parse_args()

    if not INDEX_DB.exists() or not LSH_PKL.exists():
        print(f"missing index; run scripts/provenance/index_corpus.py first", file=sys.stderr)
        return 1

    includes, excludes = load_scope()
    if not includes:
        print("no include prefixes in source-scope.toml", file=sys.stderr)
        return 1

    all_files = git_ls_files(REPO_ROOT / "gcc")
    active_excludes = [] if args.include_excluded else excludes
    active_includes = [] if args.include_excluded else includes
    candidates = [
        p for p in all_files
        if in_scope(p, active_includes, active_excludes) and is_text_candidate(p)
    ]
    if args.only:
        candidates = [p for p in candidates if any(fnmatch.fnmatch(p, pat) for pat in args.only)]
    candidates.sort()
    print(f"candidates to scan: {len(candidates)}", flush=True)

    conn = sqlite3.connect(INDEX_DB)
    conn.execute("PRAGMA query_only = ON")
    with LSH_PKL.open("rb") as handle:
        lsh = pickle.load(handle)

    severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3, "review": 2}
    min_rank = severity_rank[args.min_severity]

    findings: list[SourceFinding] = []
    scanned = 0
    started = time.monotonic()
    for rel in candidates:
        if args.limit is not None and scanned >= args.limit:
            break
        cand_path = REPO_ROOT / rel
        if not cand_path.exists():
            continue
        finding = analyze_candidate(
            conn, lsh, cand_path, rel,
            top_k=args.top_k,
            run_cpd_for=args.cpd,
            cpd_rank=args.cpd,
        )
        scanned += 1
        if finding is None:
            continue
        if args.require_silent and finding.header_class != "silent":
            continue
        if severity_rank[finding.severity] < min_rank:
            continue
        if not finding.matches:
            continue
        findings.append(finding)
        if scanned % 500 == 0:
            elapsed = time.monotonic() - started
            print(f"  scanned {scanned}/{len(candidates)} in {elapsed:.1f}s; kept {len(findings)}",
                  flush=True)

    findings.sort(key=lambda f: (-severity_rank[f.severity], -f.score, f.path))

    elapsed = time.monotonic() - started
    print(f"done: scanned={scanned} kept={len(findings)} time={elapsed:.1f}s")

    # Text report
    for index, finding in enumerate(findings[:40], start=1):
        print(f"{index:02d}. {finding.severity:8s} score={finding.score:7.2f} header={finding.header_class} {finding.path}")
        if finding.matches:
            m = finding.matches[0]
            print(f"    -> {m.project}/{m.relpath}")
            print(f"       winnow_density={m.winnow_density} shingle={m.shingle_jaccard} line={m.line_jaccard} run={m.longest_run} tlsh={m.tlsh_distance}")
            if m.cpd_clusters:
                print(f"       cpd_clusters={m.cpd_clusters} cpd_longest_lines={m.cpd_longest}")
        if finding.header_evidence:
            print(f"    header_evidence: {', '.join(finding.header_evidence)}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        serialized = [
            {
                **asdict(finding),
                "matches": [asdict(m) for m in finding.matches],
            }
            for finding in findings
        ]
        out.write_text(json.dumps({
            "scanned": scanned,
            "kept": len(findings),
            "findings": serialized,
        }, indent=2), encoding="utf-8")
        print(f"json: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
