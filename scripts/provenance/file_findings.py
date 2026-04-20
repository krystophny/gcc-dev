#!/usr/bin/env python3
"""File GitHub issues for unreviewed high/critical provenance findings.

Reads a scan_sources.py JSON report, drops findings whose `path` already
appears in .provenance/source-review.toml, keeps the rest at severity
>= high, and either prints a dry-run summary or calls `gh issue create`
one issue per finding.

Usage:
    scripts/provenance/file_findings.py REPORT.json \
        [--dry-run] [--min-severity high|critical] [--limit N]
        [--repo krystophny/gcc-dev] [--label provenance,bug]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REVIEW_TOML = REPO_ROOT / ".provenance" / "source-review.toml"

SEV_RANK = {"low": 0, "medium": 1, "review": 2, "high": 3, "critical": 4}


def load_reviewed() -> set[str]:
    if not REVIEW_TOML.exists() or tomllib is None:
        return set()
    with REVIEW_TOML.open("rb") as handle:
        data = tomllib.load(handle)
    return {entry["path"] for entry in data.get("reviewed", []) if "path" in entry}


# Title emitted by title_for(): "[SEV] provenance: <short> <- <upstream>"
# where <short> is the repo path with the leading "gcc/" stripped.
CLOSED_TITLE_RE = re.compile(
    r"^\[[^\]]+\]\s*provenance:\s*(?P<short>\S+)\s*<-\s*", re.IGNORECASE
)
# Paths referenced inside the issue body as `gcc/...`.
BODY_PATH_RE = re.compile(r"`(gcc/[^`\s]+)`")


def load_closed_issue_paths(repo: str) -> set[str]:
    """Return paths referenced by CLOSED provenance-labelled issues.

    Uses `gh issue list` to pull closed issues with the `provenance` label
    and extracts paths from both the title (filer-generated issues) and the
    body (hand-written multi-file issues).  Requires `gh` on PATH; silently
    returns an empty set on error so scanners still work offline.
    """
    try:
        result = subprocess.run(
            [
                "gh", "issue", "list",
                "--repo", repo,
                "--state", "closed",
                "--label", "provenance",
                "--limit", "500",
                "--json", "title,body",
            ],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        return set()
    paths: set[str] = set()
    for issue in issues:
        title = issue.get("title", "") or ""
        body = issue.get("body", "") or ""
        match = CLOSED_TITLE_RE.match(title)
        if match:
            short = match.group("short")
            paths.add(short if short.startswith("gcc/") else f"gcc/{short}")
        for body_match in BODY_PATH_RE.finditer(body):
            paths.add(body_match.group(1))
    return paths


def severity_ok(finding: dict, min_rank: int) -> bool:
    return SEV_RANK.get(finding.get("severity", "low"), 0) >= min_rank


def render_body(finding: dict) -> str:
    path = finding["path"]
    sev = finding["severity"]
    score = finding.get("score", 0.0)
    header_class = finding.get("header_class", "?")
    header_evidence = finding.get("header_evidence") or []
    excerpt = finding.get("header_excerpt", "")
    matches = finding.get("matches") or []
    if not matches:
        return f"No matches recorded for {path}."
    best = matches[0]

    lines = [
        "## Finding",
        "",
        f"`{path}` matches an upstream corpus file without adequate attribution.",
        "",
        "## Evidence",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| severity | {sev} |",
        f"| score | {score:.2f} |",
        f"| header class | {header_class} |",
        f"| upstream | `{best['project']}/{best['relpath']}` |",
        f"| winnow density | {best['winnow_density']} |",
        f"| matched winnows | {best['matched_winnows']} |",
        f"| longest run | {best['longest_run']} |",
        f"| shingle Jaccard | {best['shingle_jaccard']} |",
        f"| line Jaccard | {best['line_jaccard']} |",
        f"| TLSH distance | {best['tlsh_distance']} |",
    ]
    if best.get("cpd_clusters"):
        lines.append(f"| PMD CPD | {best['cpd_clusters']} clusters, longest {best['cpd_longest']} lines |")
    lines.extend([
        "",
        f"Additional corpus hits considered: {len(matches) - 1}.",
        "",
    ])

    if header_evidence:
        lines += ["## Header evidence", "", ", ".join(header_evidence), ""]
    if excerpt:
        lines += ["## Header excerpt", "", "```", excerpt, "```", ""]

    lines += textwrap.dedent(f"""
    ## Research workflow

    Follow `docs/provenance-research.md` to confirm the chain of custody
    before recommending a header or structural fix.  Record the outcome
    in `.provenance/source-review.toml` and update this issue with the
    researched chain.

    ## Audit context

    - Scanner: `scripts/provenance/scan_sources.py`
    - Corpus: `.provenance/corpus-sources.toml`
    - Research workflow: `docs/provenance-research.md`
    - Registry: `.provenance/source-review.toml`
    """).splitlines()
    return "\n".join(lines)


def title_for(finding: dict) -> str:
    path = finding["path"]
    best = finding["matches"][0]
    upstream = best["project"]
    if path.startswith("gcc/"):
        short = path[4:]
    else:
        short = path
    sev = finding["severity"]
    prefix = {"critical": "CRITICAL", "high": "HIGH"}.get(sev, sev.upper())
    return f"[{prefix}] provenance: {short} <- {upstream}"


def gh_create(finding: dict, repo: str, labels: list[str], dry_run: bool) -> str | None:
    title = title_for(finding)
    body = render_body(finding)
    if dry_run:
        print(f"--- {title}")
        print(body)
        print()
        return None
    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
    for lab in labels:
        cmd += ["--label", lab]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print(f"FAIL {title}: {exc.stderr}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="scan_sources.py --json output file")
    parser.add_argument("--repo", default="krystophny/gcc-dev")
    parser.add_argument("--label", action="append", default=[],
                        help="Labels (repeatable). Default: provenance")
    parser.add_argument("--min-severity", default="high",
                        choices=("medium", "high", "critical", "review"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.label:
        args.label = ["provenance"]

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"report not found: {report_path}", file=sys.stderr)
        return 1
    data = json.loads(report_path.read_text(encoding="utf-8"))
    findings = data.get("findings", [])
    if not isinstance(findings, list):
        print("report has no 'findings' array", file=sys.stderr)
        return 1

    reviewed = load_reviewed()
    closed = load_closed_issue_paths(args.repo)
    suppressed = reviewed | closed
    min_rank = SEV_RANK[args.min_severity]

    # dedupe: one issue per (path, upstream_project)
    seen: set[tuple[str, str]] = set()
    filtered = []
    for f in findings:
        path = f.get("path")
        if not path or path in suppressed:
            continue
        if not severity_ok(f, min_rank):
            continue
        matches = f.get("matches") or []
        if not matches:
            continue
        key = (path, matches[0]["project"])
        if key in seen:
            continue
        seen.add(key)
        filtered.append(f)

    filtered.sort(key=lambda f: (-SEV_RANK.get(f.get("severity", "low"), 0),
                                 -float(f.get("score", 0.0)), f["path"]))
    if args.limit is not None:
        filtered = filtered[: args.limit]

    print(f"findings_total={len(findings)} unreviewed={len(filtered)}"
          f" reviewed_registry={len(reviewed)} closed_issues={len(closed)}"
          f" min={args.min_severity}")

    created = 0
    for f in filtered:
        url = gh_create(f, args.repo, args.label, args.dry_run)
        if url:
            created += 1
            print(f"  {f['severity']:8s} {url}  {f['path']}")
    if not args.dry_run:
        print(f"issues_created={created}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
