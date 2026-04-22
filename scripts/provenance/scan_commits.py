#!/usr/bin/env python3
"""Commit-scoped provenance scanner.

Given a set of GCC commits, extract the files they added or modified, and
run the non-testsuite silent-imports pipeline (same LSH + fingerprint flow
as scan_sources.py) against the file contents at each commit. The result
is a report that tells you, per commit, whether any file touched in that
commit looks like a silent import from an indexed upstream corpus.

Commit selection:
  --commits FILE         read one SHA per line (lines starting with '#' are
                         ignored; anything after whitespace on a line is also
                         ignored, so `git log --oneline` output is accepted).
  --rev-range A..B       use every commit in the range (git rev-list A..B).
  --grep PATTERN         filter commits on --branch (default origin/master)
                         whose message matches PATTERN (case-insensitive).
  --branch REF           branch used by --grep (default origin/master).

For each selected commit this scanner:
  1. Runs `git show --name-status` to list added/modified files.
  2. Drops anything outside .provenance/source-scope.toml include paths,
     anything matching the exclude list, and anything is_text_candidate()
     rejects.
  3. Materialises the blob at that commit into a tempfile and calls
     analyze_candidate() from scan_sources.py (same scoring path).
  4. Also materialises the blob at the parent commit and scans it; the
     delta in severity / score is the commit-attributable risk signal.

Output:
  Text report to stdout plus optional JSON to --json. JSON groups findings
  by commit SHA and reports both the post-commit finding and the parent
  baseline so callers can sort by "risk introduced by this commit".

The scanner requires a built corpus index (corpusbin/index/corpus.sqlite
+ corpus.lsh.pkl) — run scripts/provenance/index_corpus.py first.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pickle
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.provenance._lib import is_text_candidate  # noqa: E402
from scripts.provenance.scan_sources import (  # noqa: E402
    INDEX_DB,
    LSH_PKL,
    analyze_candidate,
    in_scope,
    load_scope,
)

GCC_ROOT = REPO_ROOT / "gcc"

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3, "review": 2}


@dataclass
class CommitMeta:
    sha: str
    subject: str
    author: str
    author_email: str
    author_date: str
    trailers: list[str] = field(default_factory=list)


@dataclass
class FileResult:
    path: str
    status: str  # A, M, R100, ... (git --name-status code)
    before_severity: str = "low"
    before_score: float = 0.0
    before_finding: dict | None = None
    after_severity: str = "low"
    after_score: float = 0.0
    after_finding: dict | None = None
    severity_jump: int = 0  # rank(after) - rank(before)
    score_delta: float = 0.0


@dataclass
class CommitResult:
    commit: CommitMeta
    files_scanned: int = 0
    files_skipped_out_of_scope: int = 0
    files_skipped_binary: int = 0
    max_severity_rank: int = 0
    max_score: float = 0.0
    file_results: list[FileResult] = field(default_factory=list)


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(GCC_ROOT), *args],
        check=check,
        capture_output=True,
        text=True,
        errors="replace",
    )


def parse_commit_list(path: Path) -> list[str]:
    shas: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split()[0]
        if not re.fullmatch(r"[0-9a-fA-F]{7,40}", token):
            continue
        shas.append(token)
    return shas


def expand_commits(args) -> list[str]:
    shas: list[str] = []
    if args.commits:
        shas.extend(parse_commit_list(Path(args.commits)))
    if args.rev_range:
        result = run_git("rev-list", args.rev_range)
        shas.extend(line.strip() for line in result.stdout.splitlines() if line.strip())
    if args.grep:
        result = run_git(
            "log", args.branch, "-i", f"--grep={args.grep}", "--format=%H"
        )
        shas.extend(line.strip() for line in result.stdout.splitlines() if line.strip())
    # Preserve order (first occurrence wins) while deduplicating.
    seen: set[str] = set()
    ordered: list[str] = []
    for sha in shas:
        full = resolve_sha(sha)
        if full is None or full in seen:
            continue
        seen.add(full)
        ordered.append(full)
    return ordered


def resolve_sha(sha: str) -> str | None:
    result = run_git("rev-parse", "--verify", f"{sha}^{{commit}}", check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def load_commit_meta(sha: str) -> CommitMeta:
    # Use an unambiguous separator that will not appear in commit fields.
    sep = "\x1f"
    fmt = sep.join(["%H", "%s", "%an", "%ae", "%aI", "%(trailers:only,unfold=true)"])
    result = run_git("show", "-s", f"--format={fmt}", sha)
    parts = result.stdout.rstrip("\n").split(sep, 5)
    while len(parts) < 6:
        parts.append("")
    trailers = [line for line in parts[5].splitlines() if line.strip()]
    return CommitMeta(
        sha=parts[0],
        subject=parts[1],
        author=parts[2],
        author_email=parts[3],
        author_date=parts[4],
        trailers=trailers,
    )


def name_status(sha: str) -> list[tuple[str, str]]:
    """Return [(status, path)] for files touched by sha.

    For root commits (no parent) returns every file introduced.
    For renames (R100 old new) we keep the new path with status 'R'.
    """
    result = run_git(
        "show", "--no-renames", "--pretty=format:", "--name-status", sha
    )
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][:1]
        path = parts[-1]
        entries.append((status, path))
    return entries


def read_blob(sha: str, path: str) -> bytes | None:
    # path here is the path inside gcc/; git show wants "sha:path".
    result = run_git("show", f"{sha}:{path}", check=False)
    if result.returncode != 0:
        return None
    return result.stdout.encode("utf-8", errors="replace")


def parent_sha(sha: str) -> str | None:
    result = run_git("rev-parse", f"{sha}^", check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def scan_blob(
    conn: sqlite3.Connection,
    lsh,
    blob: bytes,
    rel_path: str,
    top_k: int,
) -> dict | None:
    if blob is None or len(blob) < 256:
        return None
    with tempfile.NamedTemporaryFile(
        prefix="provcommit-", suffix="-" + Path(rel_path).name, delete=False
    ) as handle:
        handle.write(blob)
        tmp_path = Path(handle.name)
    try:
        finding = analyze_candidate(
            conn, lsh, tmp_path, rel_path,
            top_k=top_k,
            run_cpd_for=0,
            cpd_rank=0,
        )
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass
    if finding is None or not finding.matches:
        return None
    return {
        **asdict(finding),
        "matches": [asdict(m) for m in finding.matches],
    }


def severity_from_finding(finding: dict | None) -> tuple[str, float]:
    if not finding:
        return ("low", 0.0)
    return (finding.get("severity", "low"), float(finding.get("score", 0.0)))


def scan_commit(
    sha: str,
    conn: sqlite3.Connection,
    lsh,
    includes: list[str],
    excludes: list[tuple[str, str]],
    top_k: int,
) -> CommitResult:
    meta = load_commit_meta(sha)
    result = CommitResult(commit=meta)
    entries = name_status(sha)
    parent = parent_sha(sha)

    for status, path in entries:
        # git --name-status paths are gcc-repo relative; in_scope expects
        # the meta-repo prefix "gcc/".
        scoped_path = f"gcc/{path}"
        if not in_scope(scoped_path, includes, excludes):
            result.files_skipped_out_of_scope += 1
            continue
        if not is_text_candidate(scoped_path):
            result.files_skipped_binary += 1
            continue

        file_res = FileResult(path=scoped_path, status=status)

        result.files_scanned += 1
        before_finding = None
        if status != "A" and parent is not None:
            before_blob = read_blob(parent, path)
            before_finding = scan_blob(conn, lsh, before_blob, scoped_path, top_k)
        after_blob = read_blob(sha, path)
        after_finding = scan_blob(conn, lsh, after_blob, scoped_path, top_k)

        if before_finding is None and after_finding is None:
            # File was in scope but neither parent nor post-commit blob
            # produced a corpus hit — nothing to record.
            continue

        file_res.before_severity, file_res.before_score = severity_from_finding(before_finding)
        file_res.after_severity, file_res.after_score = severity_from_finding(after_finding)
        file_res.before_finding = before_finding
        file_res.after_finding = after_finding
        file_res.severity_jump = (
            SEVERITY_RANK[file_res.after_severity]
            - SEVERITY_RANK[file_res.before_severity]
        )
        file_res.score_delta = file_res.after_score - file_res.before_score
        result.file_results.append(file_res)
        result.max_severity_rank = max(
            result.max_severity_rank, SEVERITY_RANK[file_res.after_severity]
        )
        result.max_score = max(result.max_score, file_res.after_score)
    return result


def format_severity(rank: int) -> str:
    for name, value in SEVERITY_RANK.items():
        if value == rank:
            return name
    return "low"


def print_text_report(results: list[CommitResult]) -> None:
    by_risk = sorted(
        results,
        key=lambda r: (-r.max_severity_rank, -r.max_score, r.commit.author_date),
    )
    print(f"commits scanned: {len(results)}")
    flagged = [r for r in results if r.file_results]
    print(f"commits with corpus matches: {len(flagged)}")
    for idx, res in enumerate(by_risk, start=1):
        if not res.file_results:
            continue
        sev = format_severity(res.max_severity_rank)
        print(
            f"\n{idx:02d}. [{sev:8s} max_score={res.max_score:6.2f}] "
            f"{res.commit.sha[:12]} {res.commit.author_date[:10]} {res.commit.subject}"
        )
        print(f"    author: {res.commit.author} <{res.commit.author_email}>")
        for fr in sorted(
            res.file_results,
            key=lambda f: (-SEVERITY_RANK[f.after_severity], -f.after_score),
        ):
            delta_marker = " *NEW*" if fr.severity_jump > 0 else ""
            print(
                f"    - {fr.status} {fr.path}"
                f" after={fr.after_severity}/{fr.after_score:.2f}"
                f" before={fr.before_severity}/{fr.before_score:.2f}"
                f" delta={fr.score_delta:+.2f}{delta_marker}"
            )
            if fr.after_finding and fr.after_finding.get("matches"):
                m = fr.after_finding["matches"][0]
                print(
                    f"      -> {m['project']}/{m['relpath']}"
                    f" density={m['winnow_density']} shingle={m['shingle_jaccard']}"
                    f" line={m['line_jaccard']} run={m['longest_run']}"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commits", help="File with one commit SHA per line.")
    parser.add_argument("--rev-range", help="git rev-list range, e.g. A..B.")
    parser.add_argument(
        "--grep",
        help="Filter commits on --branch whose message matches PATTERN (case-insensitive).",
    )
    parser.add_argument(
        "--branch",
        default="origin/master",
        help="Branch used by --grep (default: origin/master).",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--min-severity",
        choices=("low", "medium", "high", "critical", "review"),
        default="low",
        help="Suppress commit results whose max severity rank is below this.",
    )
    parser.add_argument("--json", help="Write JSON report to this path.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if not any([args.commits, args.rev_range, args.grep]):
        parser.error("provide at least one of --commits, --rev-range, --grep")

    if not INDEX_DB.exists() or not LSH_PKL.exists():
        print("missing corpus index; run scripts/provenance/index_corpus.py first",
              file=sys.stderr)
        return 1

    includes, excludes = load_scope()
    if not includes:
        print("no include prefixes in source-scope.toml", file=sys.stderr)
        return 1

    shas = expand_commits(args)
    if args.limit is not None:
        shas = shas[: args.limit]
    print(f"commits to scan: {len(shas)}", flush=True)
    if not shas:
        return 0

    conn = sqlite3.connect(INDEX_DB)
    conn.execute("PRAGMA query_only = ON")
    with LSH_PKL.open("rb") as handle:
        lsh = pickle.load(handle)

    min_rank = SEVERITY_RANK[args.min_severity]
    results: list[CommitResult] = []
    started = time.monotonic()
    for i, sha in enumerate(shas, start=1):
        res = scan_commit(sha, conn, lsh, includes, excludes, args.top_k)
        results.append(res)
        if i % 10 == 0 or i == len(shas):
            elapsed = time.monotonic() - started
            print(f"  {i}/{len(shas)} done ({elapsed:.1f}s)", flush=True)

    filtered = [
        r for r in results
        if not r.file_results or r.max_severity_rank >= min_rank
    ]
    print_text_report(filtered)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        serialized = {
            "branch": args.branch,
            "grep": args.grep,
            "rev_range": args.rev_range,
            "commits_scanned": len(results),
            "results": [
                {
                    "commit": asdict(r.commit),
                    "files_scanned": r.files_scanned,
                    "files_skipped_out_of_scope": r.files_skipped_out_of_scope,
                    "files_skipped_binary": r.files_skipped_binary,
                    "max_severity": format_severity(r.max_severity_rank),
                    "max_score": round(r.max_score, 2),
                    "file_results": [asdict(fr) for fr in r.file_results],
                }
                for r in results
            ],
        }
        out.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
        print(f"json: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
