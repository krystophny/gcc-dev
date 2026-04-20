#!/usr/bin/env python3
"""Upstream-side silent-imports scanner.

Walks every file under corpusbin/src/<project>/, classifies the header for
GCC/FSF attribution, fingerprints the content, and probes the GCC index
(corpusbin/index/gcc.*) for near-duplicates. Silent upstream header plus a
strong GCC match is the dangerous class: external project has lifted GCC
code without retaining the Runtime Library Exception / FSF copyright.

This is the *reverse* of scripts/provenance/scan_sources.py. Between the
two we cover both directions of silent copying.

Prereq: `python3 scripts/provenance/index_gcc.py` has produced
corpusbin/index/gcc.sqlite and corpusbin/index/gcc.lsh.pkl.
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import tlsh

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.provenance._lib import (  # noqa: E402
    is_text_candidate,
    line_similarity,
    read_prefix,
    shingle_similarity,
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

CORPUS_ROOT = REPO_ROOT / "corpusbin" / "src"
GCC_INDEX_DB = REPO_ROOT / "corpusbin" / "index" / "gcc.sqlite"
GCC_LSH_PKL = REPO_ROOT / "corpusbin" / "index" / "gcc.lsh.pkl"
GCC_ROOT = REPO_ROOT / "gcc"

# Heuristics for "upstream header attributes to GCC/FSF".
GCC_ATTRIBUTION_PATTERNS = (
    re.compile(r"\bGCC\b"),
    re.compile(r"GNU\s+Compiler\s+Collection", re.IGNORECASE),
    re.compile(r"Free\s+Software\s+Foundation", re.IGNORECASE),
    re.compile(r"Runtime\s+Library\s+Exception", re.IGNORECASE),
    re.compile(r"\blibgcc\b"),
    re.compile(r"\blibstdc\+\+\b", re.IGNORECASE),
    re.compile(r"\blibgomp\b"),
    re.compile(r"\blibgfortran\b"),
    re.compile(r"\blibquadmath\b"),
    re.compile(r"\blibiberty\b"),
    re.compile(r"\blibsupc\+\+", re.IGNORECASE),
    re.compile(r"\blibobjc\b"),
    re.compile(r"\blibitm\b"),
    re.compile(r"\blibatomic\b"),
    re.compile(r"\blibbacktrace\b"),
    re.compile(r"\blibssp\b"),
    re.compile(r"\blibvtv\b"),
    re.compile(r"kept\s+in\s+sync\s+with\s+libgcc", re.IGNORECASE),
    re.compile(r"\bgcc\.gnu\.org", re.IGNORECASE),
    re.compile(r"sourceware\.org/gcc", re.IGNORECASE),
)


@dataclass
class Match:
    relpath: str
    tokens: int
    winnow_density: float
    matched_winnows: int
    longest_run: int
    shingle_jaccard: float
    line_jaccard: float
    tlsh_distance: int


@dataclass
class Finding:
    project: str
    relpath: str
    bytes: int
    tokens: int
    header_class: str
    header_evidence: list[str]
    header_excerpt: str
    severity: str = "low"
    score: float = 0.0
    matches: list[Match] = field(default_factory=list)


def upstream_has_gcc_attribution(header: str) -> tuple[bool, list[str]]:
    hits: list[str] = []
    for pat in GCC_ATTRIBUTION_PATTERNS:
        m = pat.search(header)
        if m:
            hits.append(m.group(0))
    return (bool(hits), hits)


def unpack_hashes(blob: bytes) -> list[int]:
    return [int.from_bytes(blob[i:i + 8], "little", signed=True)
            for i in range(0, len(blob), 8)]


def classify(header_silent: bool, best: Match | None) -> tuple[str, float]:
    if best is None:
        return ("low", 0.0)
    d = best.winnow_density
    s = best.shingle_jaccard
    line = best.line_jaccard
    score = 100.0 * d + 60.0 * s + 0.25 * best.longest_run
    LINE_FLOOR_HIGH = 0.06
    if header_silent and line < LINE_FLOOR_HIGH:
        if d >= 0.25 and s >= 0.20:
            return ("medium", score * 0.6)
        return ("low", score * 0.3)
    if not header_silent:
        # Upstream attributes GCC -> just a review signal, not a defect.
        if d >= 0.85 or s >= 0.85:
            return ("review", score)
        if d >= 0.60 or s >= 0.70:
            return ("review", score * 0.8)
        return ("low", score * 0.5)
    strong = d >= 0.60 and s >= 0.45
    partial = d >= 0.35 and s >= 0.30
    weak = d >= 0.25 and s >= 0.20
    if strong or s >= 0.70:
        return ("critical", score + 50)
    if partial or s >= 0.45:
        return ("high", score + 20)
    if weak or s >= 0.30:
        return ("medium", score)
    return ("low", score)


def iter_corpus_files():
    for project_dir in sorted(CORPUS_ROOT.iterdir()):
        if not project_dir.is_dir():
            continue
        project = project_dir.name
        for path in project_dir.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue
            if path.name == ".corpus-sha":
                continue
            try:
                rel = path.relative_to(project_dir).as_posix()
            except ValueError:
                continue
            if not is_text_candidate(rel):
                continue
            yield project, rel, path


def analyze(
    conn: sqlite3.Connection,
    lsh,
    project: str,
    rel: str,
    path: Path,
    top_k: int,
) -> Finding | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 256:
        return None
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return None
    fp = fingerprint_text(text, k=DEFAULT_K, window=DEFAULT_WINDOW,
                          num_perm=DEFAULT_MINHASH_PERM)
    if fp.token_count < 80:
        return None

    prefix = read_prefix(path, lines=60)
    has_marker, evidence = upstream_has_gcc_attribution(prefix)

    finding = Finding(
        project=project,
        relpath=rel,
        bytes=len(data),
        tokens=fp.token_count,
        header_class="marked" if has_marker else "silent",
        header_evidence=evidence,
        header_excerpt="\n".join(line.rstrip() for line in prefix.splitlines()[:8]),
    )

    try:
        cand_mh = minhash_from_bytes(fp.minhash_bytes)
    except ValueError:
        return finding

    hits = lsh.query(cand_mh)
    if not hits:
        return finding

    try:
        cand_tlsh = tlsh.hash(data)
    except Exception:
        cand_tlsh = ""

    cur = conn.cursor()
    scored: list[tuple[float, Match]] = []
    # Fast prefilter: compute winnow density against every LSH hit first
    # (cheap), sort by density, then do the expensive shingle/line
    # computation on just the top few. Without this, a corpus file that
    # LSH-collides against dozens of GCC files fans out into O(hits)
    # O(N^2) shingle computations.
    DENSITY_PREFILTER = 0.10
    prelim: list[tuple[float, str, int, str, list[int], int]] = []
    for hit_id in hits[: max(top_k * 4, 20)]:
        row = cur.execute(
            "SELECT relpath, tokens, tlsh, winnow_hashes FROM files WHERE id=?",
            (int(hit_id),),
        ).fetchone()
        if row is None:
            continue
        gcc_rel, gcc_tokens, gcc_tlsh, gcc_fp_blob = row
        gcc_fps = unpack_hashes(gcc_fp_blob)
        matched, density = winnow_density(fp.winnow_hashes, gcc_fps)
        if matched == 0 or density < DENSITY_PREFILTER:
            continue
        prelim.append((density, gcc_rel, gcc_tokens, gcc_tlsh, gcc_fps, matched))
    prelim.sort(key=lambda item: -item[0])
    # Only the top 2*top_k survivors get full shingle/line work.
    for density, gcc_rel, gcc_tokens, gcc_tlsh, gcc_fps, matched in prelim[: max(top_k * 2, 6)]:
        gcc_path = GCC_ROOT / gcc_rel
        if not gcc_path.exists():
            continue
        try:
            gcc_text = gcc_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        s_j = shingle_similarity(text, gcc_text)
        l_j = line_similarity(text, gcc_text)
        gcc_positions = list(range(len(gcc_fps)))
        run = longest_run(fp.winnow_positions, gcc_positions,
                          fp.winnow_hashes, gcc_fps)
        try:
            dist = tlsh.diff(cand_tlsh, gcc_tlsh) if cand_tlsh and gcc_tlsh else -1
        except Exception:
            dist = -1
        match = Match(
            relpath=gcc_rel,
            tokens=gcc_tokens,
            winnow_density=round(density, 4),
            matched_winnows=matched,
            longest_run=run,
            shingle_jaccard=round(s_j, 4),
            line_jaccard=round(l_j, 4),
            tlsh_distance=dist,
        )
        rank = density + s_j + (run / 200.0)
        scored.append((rank, match))
    scored.sort(key=lambda item: -item[0])
    finding.matches = [m for _r, m in scored[:top_k]]

    if finding.matches:
        severity, score = classify(not has_marker, finding.matches[0])
        finding.severity = severity
        finding.score = round(score, 2)
    return finding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--require-silent", action="store_true",
                        help="Only report findings where the upstream header lacks "
                             "GCC/FSF attribution.")
    parser.add_argument("--min-severity",
                        choices=("low", "medium", "high", "critical", "review"),
                        default="medium")
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after N candidates (smoke tests).")
    parser.add_argument("--project", action="append", default=[],
                        help="Restrict to one or more corpus projects")
    parser.add_argument("--json", help="Write full JSON report to this path.")
    args = parser.parse_args()

    if not GCC_INDEX_DB.exists() or not GCC_LSH_PKL.exists():
        print("GCC index missing; run scripts/provenance/index_gcc.py first",
              file=sys.stderr)
        return 1

    conn = sqlite3.connect(GCC_INDEX_DB)
    conn.execute("PRAGMA query_only = ON")
    with GCC_LSH_PKL.open("rb") as handle:
        lsh = pickle.load(handle)

    severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3, "review": 2}
    min_rank = severity_rank[args.min_severity]

    findings: list[Finding] = []
    scanned = 0
    started = time.monotonic()
    for project, rel, path in iter_corpus_files():
        if args.project and project not in args.project:
            continue
        if args.limit is not None and scanned >= args.limit:
            break
        scanned += 1
        f = analyze(conn, lsh, project, rel, path, top_k=args.top_k)
        if f is None:
            continue
        if args.require_silent and f.header_class != "silent":
            continue
        if severity_rank[f.severity] < min_rank:
            continue
        if not f.matches:
            continue
        findings.append(f)
        if scanned % 500 == 0:
            elapsed = time.monotonic() - started
            print(f"  scanned {scanned} in {elapsed:.1f}s; kept {len(findings)}",
                  flush=True)

    findings.sort(key=lambda f: (-severity_rank[f.severity], -f.score,
                                  f.project, f.relpath))

    elapsed = time.monotonic() - started
    print(f"done: scanned={scanned} kept={len(findings)} time={elapsed:.1f}s")

    for i, f in enumerate(findings[:60], 1):
        m = f.matches[0] if f.matches else None
        print(f"{i:02d}. {f.severity:8s} score={f.score:7.2f} header={f.header_class} "
              f"{f.project}/{f.relpath}")
        if m:
            print(f"    -> gcc/{m.relpath}")
            print(f"       density={m.winnow_density} shingle={m.shingle_jaccard} "
                  f"line={m.line_jaccard} run={m.longest_run} tlsh={m.tlsh_distance}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        serialized = [
            {**asdict(f), "matches": [asdict(m) for m in f.matches]}
            for f in findings
        ]
        out.write_text(
            json.dumps({"scanned": scanned, "kept": len(findings),
                        "findings": serialized}, indent=2),
            encoding="utf-8",
        )
        print(f"json: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
