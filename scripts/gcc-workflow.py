#!/usr/bin/env python3
"""Backport-aware workflow helpers for GCC Fortran bug work."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
import xmlrpc.client
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent.parent
PR_ROOT = ROOT / "pr"
GCC_DIR = ROOT / "gcc"
WORKTREE_ROOT = ROOT / "gcc-worktrees"

ACTIVE_BRANCHES: Dict[str, Dict[str, str]] = {
    "gcc-15": {
        "ref": "upstream/releases/gcc-15",
        "worktree": str(WORKTREE_ROOT / "gcc-15"),
        "build": str(ROOT / "gcc-build-gcc15"),
    },
    "gcc-14": {
        "ref": "upstream/releases/gcc-14",
        "worktree": str(WORKTREE_ROOT / "gcc-14"),
        "build": str(ROOT / "gcc-build-gcc14"),
    },
    "gcc-13": {
        "ref": "upstream/releases/gcc-13",
        "worktree": str(WORKTREE_ROOT / "gcc-13"),
        "build": str(ROOT / "gcc-build-gcc13"),
    },
}

BUGZILLA_XMLRPC = "https://gcc.gnu.org/bugzilla/xmlrpc.cgi"

DEFAULT_BRANCH_STATE = {
    "reproduces": None,
    "backport_candidate": None,
    "apply_mode": "unknown",
    "branch_commit": None,
    "branch_patch": None,
    "targeted_tests": "not-run",
    "full_suite": "not-run",
    "notes": "",
}

UTC = _dt.timezone.utc

REGRESSION_OVERRIDES = {
    102430: True,
    106946: True,
    122491: True,
    123255: True,
    123868: True,
    123947: True,
    123949: True,
    124208: True,
    124235: True,
}

SEVERITY_OVERRIDES = {
    102430: "ice-on-valid",
    102459: "ice-on-valid",
    102596: "ice-on-valid",
    106946: "ice-on-invalid",
    110877: "wrong-code",
    120286: "runtime-crash",
    120723: "ice-on-valid",
    122491: "ice-on-invalid",
    123255: "wrong-code",
    123868: "wrong-code",
    123947: "ice-on-valid",
    123949: "ice-on-valid",
    124208: "wrong-code",
    124235: "ice-on-valid",
    82721: "ice-on-invalid",
    95338: "ice-on-valid",
}

VALIDITY_OVERRIDES = {
    102430: "valid-code",
    102459: "valid-code",
    102596: "valid-code",
    106946: "invalid-code",
    110877: "valid-code",
    120286: "valid-code",
    120723: "valid-code",
    122491: "invalid-code",
    123255: "valid-code",
    123868: "valid-code",
    123947: "valid-code",
    123949: "valid-code",
    124208: "valid-code",
    124235: "valid-code",
    82721: "invalid-code",
    95338: "valid-code",
}

VALIDATION_OVERRIDES = {
    102430: {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-fopenmp",
            "-c",
            "pr/102430/reproducer.f90",
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "nonzero",
            "contains_any": ["Sorry, not yet supported", "not yet supported"],
            "not_contains": ["internal compiler error"],
        },
    },
    106946: {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-fsyntax-only",
            "pr/106946/reproducer.f90",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "nonzero",
            "contains_any": ["Syntax error in data declaration", "Invalid character"],
            "not_contains": ["internal compiler error"],
        },
    },
    110877: {
        "kind": "run",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "pr/110877/reproducer.f90",
            "-o",
            "/tmp/pr110877",
        ],
        "run": ["/tmp/pr110877"],
        "env": {},
    },
    120286: {
        "kind": "run",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-fopenmp",
            "pr/120286/reproducer.f90",
            "-o",
            "/tmp/pr120286",
        ],
        "run": ["/tmp/pr120286"],
        "env": {"OMP_NUM_THREADS": "2"},
    },
    122491: {
        "kind": "special-env",
        "reason": "requires sanitizer-instrumented branch compiler to observe the UAF",
    },
    123255: {
        "kind": "special-env",
        "reason": "requires NVPTX OpenACC runtime/offload execution to reproduce the size bug",
    },
    123868: {
        "kind": "special-env",
        "reason": "requires Valgrind or equivalent leak checking to validate the regression",
    },
    123947: {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-c",
            "pr/123947/reproducer-reduced.f90",
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "zero",
            "contains_any": [],
            "not_contains": ["internal compiler error"],
        },
    },
    123949: {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-c",
            "-w",
            "pr/123949/reproducer.f90",
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "zero",
            "contains_any": [],
            "not_contains": ["internal compiler error"],
        },
    },
    124208: {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-c",
            "pr/124208/reproducer.f90",
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "zero",
            "contains_any": [],
            "not_contains": ["internal compiler error"],
        },
    },
    124235: {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-c",
            "pr/124235/reproducer.f90",
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "zero",
            "contains_any": [],
            "not_contains": ["internal compiler error"],
        },
    },
}


class WorkflowError(RuntimeError):
    """Raised for user-facing workflow errors."""


def run(
    cmd: List[str],
    *,
    cwd: Optional[Path] = None,
    check: bool = True,
    capture: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        capture_output=capture,
        env={**os.environ, **(env or {})},
    )
    if check and proc.returncode != 0:
        raise WorkflowError(
            "command failed: {}\nstdout:\n{}\nstderr:\n{}".format(
                " ".join(shlex.quote(x) for x in cmd),
                proc.stdout,
                proc.stderr,
            )
        )
    return proc


def pr_dirs(selected: Optional[Iterable[str]] = None) -> List[Path]:
    dirs = sorted(
        p for p in PR_ROOT.iterdir() if p.is_dir() and p.name.isdigit()
    )
    if not selected:
        return dirs
    wanted = {str(x) for x in selected}
    return [p for p in dirs if p.name in wanted]


def status_pr_dirs(selected: Optional[Iterable[str]] = None) -> List[Path]:
    return [p for p in pr_dirs(selected) if (p / "status.json").exists()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_status_line(readme: str) -> str:
    match = re.search(r"^\s*[-*]\s+\*\*Status:\*\*\s+(.+)$", readme, re.M)
    return match.group(1).strip() if match else ""


def parse_first_match(pattern: str, text: str) -> Optional[str]:
    match = re.search(pattern, text, re.M)
    return match.group(1).strip() if match else None


def parse_bugzilla(readme: str, default_pr: int) -> int:
    bug = parse_first_match(r"show_bug\.cgi\?id=(\d+)", readme)
    return int(bug) if bug else default_pr


def parse_github_issue(readme: str) -> Optional[int]:
    gh = parse_first_match(r"github\.com/[^/]+/[^/]+/issues/(\d+)", readme)
    return int(gh) if gh else None


def parse_trunk_commit(readme: str) -> Optional[str]:
    patterns = [
        r"GCC commit:\s*`([0-9a-f]{7,40})`",
        r"commit `([0-9a-f]{7,40})`",
        r"commit ([0-9a-f]{7,40})",
        r"origin/[A-Za-z0-9_.-]+`\s*\(`([0-9a-f]{7,40})`\)",
    ]
    for pattern in patterns:
        value = parse_first_match(pattern, readme)
        if value:
            return value
    return None


def parse_title(readme: str, fallback: str) -> str:
    heading = parse_first_match(r"^#\s+(.+)$", readme)
    if not heading:
        return fallback
    normalized = re.sub(r"^(Bug|PR)\s*\d+\s*[:\-]?\s*", "", heading).strip()
    return normalized or fallback


def parse_branch_name(readme: str) -> Optional[str]:
    patterns = [
        r"Branch:\s*`([^`]+)`",
        r"branch `([^`]+)`",
    ]
    for pattern in patterns:
        value = parse_first_match(pattern, readme)
        if value:
            return value
    return None


def parse_patch_name(readme: str, patch_files: List[str], existing_patch: Optional[str]) -> Optional[str]:
    mentioned = re.findall(r"(0001-[A-Za-z0-9_.+-]+\.patch)", readme)
    for patch in reversed(mentioned):
        if patch in patch_files:
            return patch
    if existing_patch and existing_patch in patch_files:
        return existing_patch
    return patch_files[-1] if patch_files else None


def parse_fix_status(status_line: str, pr_dir: Path) -> str:
    upper = status_line.upper()
    if "MERGED" in upper:
        return "merged"
    if "WORKSFORME" in upper or "CLOSED" in upper:
        return "worksforme"
    if "PATCH READY" in upper:
        return "patch-ready"
    if "PENDING" in upper and list(pr_dir.glob("0001-*.patch")):
        return "patch-ready"
    if status_line:
        return "open"
    if list(pr_dir.glob("0001-*.patch")):
        return "patch-ready"
    return "open"


def parse_submission_status(status_line: str) -> Dict[str, bool]:
    lower = status_line.lower()
    return {
        "on_bugzilla": "bugzilla" in lower and "awaiting" not in lower,
        "on_mailing_list": "mailing-list" in lower or "mailing list" in lower,
        "sent": False,
    }


def infer_regression(pr: int, readme: str, status_line: str, bugzilla: Dict[str, Any]) -> bool:
    if pr in REGRESSION_OVERRIDES:
        return REGRESSION_OVERRIDES[pr]
    title = parse_first_match(r"^#\s+(.+)$", readme) or ""
    first_block = "\n".join(readme.splitlines()[:20])
    text = " ".join(
        x
        for x in [
            title,
            first_block,
            status_line,
            bugzilla.get("summary", ""),
            " ".join(bugzilla.get("keywords", [])),
        ]
        if x
    ).lower()
    return bool(re.search(r"\bregression\b", text))


def infer_severity(pr: int, readme: str) -> str:
    if pr in SEVERITY_OVERRIDES:
        return SEVERITY_OVERRIDES[pr]
    lower = readme.lower()
    if "wrong-code" in lower:
        return "wrong-code"
    if "double free" in lower or "segfault" in lower or "runtime" in lower:
        return "runtime-crash"
    if "ice" in lower:
        if "invalid" in lower:
            return "ice-on-invalid"
        return "ice-on-valid"
    return "other"


def infer_validity_class(pr: int, severity: str) -> str:
    if pr in VALIDITY_OVERRIDES:
        return VALIDITY_OVERRIDES[pr]
    return "invalid-code" if severity == "ice-on-invalid" else "valid-code"


def default_validation(pr: int, pr_dir: Path) -> Dict[str, Any]:
    if pr in VALIDATION_OVERRIDES:
        return VALIDATION_OVERRIDES[pr]
    reproducer = pr_dir / "reproducer.f90"
    candidate = reproducer
    if not candidate.exists():
        alternatives = sorted(
            p
            for p in pr_dir.glob("*.f90")
            if "attachment" not in p.name
        )
        if alternatives:
            candidate = alternatives[0]
    return {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-c",
            str(candidate.relative_to(ROOT)),
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
        "baseline": {
            "exit": "nonzero",
            "contains_any": ["internal compiler error", "ICE in"],
            "not_contains": [],
        },
        "fixed": {
            "exit": "zero",
            "contains_any": [],
            "not_contains": ["internal compiler error"],
        },
    }


def load_status(pr_dir: Path) -> Dict[str, Any]:
    path = pr_dir / "status.json"
    if not path.exists():
        raise WorkflowError(f"missing metadata: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bugzilla_lookup(pr: int) -> Dict[str, Any]:
    server = xmlrpc.client.ServerProxy(BUGZILLA_XMLRPC)
    response = server.Bug.get(
        {
            "ids": [pr],
            "include_fields": [
                "id",
                "summary",
                "status",
                "resolution",
                "keywords",
            ],
        }
    )
    bugs = response.get("bugs", [])
    if not bugs:
        return {}
    bug = bugs[0]
    return {
        "summary": bug.get("summary"),
        "status": bug.get("status"),
        "resolution": bug.get("resolution"),
        "keywords": bug.get("keywords", []),
        "refreshed_at": timestamp(),
    }


def ensure_branch_matrix(existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    matrix = existing or {}
    for branch in ACTIVE_BRANCHES:
        current = dict(DEFAULT_BRANCH_STATE)
        current.update(matrix.get(branch, {}))
        matrix[branch] = current
    return matrix


def build_status(pr_dir: Path, refresh_bugzilla: bool, existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    pr = int(pr_dir.name)
    readme = read_text(pr_dir / "README.md")
    status_line = parse_status_line(readme)
    bugzilla_info = existing.get("bugzilla", {}) if existing else {}
    if refresh_bugzilla:
        try:
            bugzilla_info = bugzilla_lookup(pr)
        except Exception as exc:  # pragma: no cover - network-dependent
            bugzilla_info = {**bugzilla_info, "lookup_error": str(exc)}
    bugzilla = parse_bugzilla(readme, pr)
    patch_files = sorted(p.name for p in pr_dir.glob("0001-*.patch"))
    existing_patch = existing.get("trunk", {}).get("patch") if existing else None
    trunk_commit = parse_trunk_commit(readme)
    fix_status = parse_fix_status(status_line, pr_dir)
    severity = infer_severity(pr, readme)
    metadata = {
        "pr": pr,
        "title": parse_title(readme, pr_dir.name),
        "bugzilla": {
            "id": bugzilla,
            "url": f"https://gcc.gnu.org/bugzilla/show_bug.cgi?id={bugzilla}",
            **bugzilla_info,
        },
        "github_issue": parse_github_issue(readme),
        "fix_status": fix_status,
        "submission_status": parse_submission_status(status_line),
        "trunk": {
            "branch": parse_branch_name(readme),
            "commit": trunk_commit,
            "patch": parse_patch_name(readme, patch_files, existing_patch),
        },
        "classification": {
            "regression": infer_regression(pr, readme, status_line, bugzilla_info),
            "severity": severity,
            "validity_class": infer_validity_class(pr, severity),
        },
        "validation": default_validation(pr, pr_dir),
        "artifacts": {
            "maintainer_summary": "submission/maintainer-summary.md",
            "bugzilla_comment": "submission/bugzilla-comment.txt",
            "mailing_list_cover": "submission/mailing-list-cover.txt",
        },
        "backports": ensure_branch_matrix(existing.get("backports") if existing else None),
        "notes": existing.get("notes", "") if existing else "",
        "updated_at": timestamp(),
    }
    return metadata


def sync_metadata(paths: List[Path], refresh_bugzilla: bool) -> None:
    for pr_dir in paths:
        existing = {}
        status_path = pr_dir / "status.json"
        if status_path.exists():
            existing = json.loads(status_path.read_text(encoding="utf-8"))
        data = build_status(pr_dir, refresh_bugzilla, existing)
        write_json(status_path, data)
        print(f"updated {status_path.relative_to(ROOT)}")


def load_all_metadata(paths: List[Path]) -> List[Dict[str, Any]]:
    return [load_status(path) for path in paths]


def bool_text(value: Optional[bool]) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def branch_row(branch: str, info: Dict[str, Any]) -> str:
    return (
        f"| {branch} | {bool_text(info.get('reproduces'))} | "
        f"{bool_text(info.get('backport_candidate'))} | {info.get('apply_mode', 'unknown')} | "
        f"{info.get('targeted_tests', 'not-run')} | {info.get('full_suite', 'not-run')} |"
    )


def maintainer_summary(meta: Dict[str, Any]) -> str:
    lines = [
        f"# PR{meta['pr']} Maintainer Summary",
        "",
        f"- **Bugzilla:** {meta['bugzilla']['url']}",
        f"- **GitHub issue:** "
        + (
            f"https://github.com/krystophny/gcc-dev/issues/{meta['github_issue']}"
            if meta.get("github_issue")
            else "n/a"
        ),
        f"- **Fix status:** {meta['fix_status']}",
        f"- **Regression:** {'yes' if meta['classification']['regression'] else 'no'}",
        f"- **Severity:** {meta['classification']['severity']}",
        f"- **Validity class:** {meta['classification']['validity_class']}",
        f"- **Trunk commit:** {meta['trunk']['commit'] or 'n/a'}",
        f"- **Trunk patch:** {meta['trunk']['patch'] or 'n/a'}",
        "",
        "## Active Release Branch Matrix",
        "",
        "| Branch | Reproduces | Candidate | Apply mode | Targeted tests | Full suite |",
        "|--------|------------|-----------|------------|----------------|------------|",
    ]
    for branch, info in meta["backports"].items():
        lines.append(branch_row(branch, info))
    lines.extend(
        [
            "",
            "## Risk Summary",
            "",
            f"This is a `{meta['classification']['severity']}` fix against "
            f"`{meta['classification']['validity_class']}`. Branch-specific patch data and "
            "test evidence live in `status.json` and the `backports/` subdirectories.",
            "",
        ]
    )
    if meta.get("notes"):
        lines.extend(["## Notes", "", meta["notes"], ""])
    return "\n".join(lines)


def submission_placeholder(kind: str, meta: Dict[str, Any], branch: str = "trunk") -> str:
    patch = (
        meta["trunk"].get("patch")
        if branch == "trunk"
        else meta["backports"][branch].get("branch_patch") or meta["trunk"].get("patch")
    ) or "missing patch"
    branch_note = "trunk" if branch == "trunk" else branch
    return textwrap.dedent(
        f"""\
        TODO: write the {kind} text for PR{meta['pr']} ({branch_note}).

        This file is used verbatim by the submission helper.
        Replace this placeholder before running submit.

        Bugzilla: {meta['bugzilla']['url']}
        Patch: {patch}
        """
    ).strip() + "\n"


def submission_text_path(pr_dir: Path, basename: str, branch: str = "trunk") -> Path:
    submission_dir = pr_dir / "submission"
    if branch != "trunk":
        stem, suffix = os.path.splitext(basename)
        candidate = submission_dir / f"{stem}-{branch}{suffix}"
        if candidate.exists():
            return candidate
    return submission_dir / basename


def ensure_submission_text(pr_dir: Path, meta: Dict[str, Any], basename: str, kind: str, branch: str = "trunk") -> Path:
    path = submission_text_path(pr_dir, basename, branch)
    if path.exists():
        return path
    path.write_text(submission_placeholder(kind, meta, branch), encoding="utf-8")
    return path


def is_generated_submission_text(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith("TODO:"):
        return True
    generated_prefixes = (
        "Proposed trunk fix for PR",
        "Backport candidate for ",
    )
    if stripped.startswith(generated_prefixes):
        return True
    if re.match(r"^(?:\[[^\]]+\]\s+)?PR\d+\s+submission packet\b", stripped):
        return True
    return "This packet was generated from the meta-repo workflow" in stripped


def load_submission_text(pr_dir: Path, meta: Dict[str, Any], basename: str, kind: str, branch: str = "trunk") -> Tuple[Path, str]:
    path = submission_text_path(pr_dir, basename, branch)
    if not path.exists():
        raise WorkflowError(
            f"PR{meta['pr']} is missing {path.relative_to(ROOT)}; write the {kind} text first"
        )
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise WorkflowError(
            f"PR{meta['pr']} has an empty {path.relative_to(ROOT)}; write the {kind} text first"
        )
    if is_generated_submission_text(text):
        raise WorkflowError(
            f"PR{meta['pr']} still has placeholder or autogenerated text in {path.relative_to(ROOT)}; replace it before submission"
        )
    return path, text + "\n"


def render_packet(meta: Dict[str, Any]) -> None:
    pr_dir = PR_ROOT / str(meta["pr"])
    submission_dir = pr_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)
    (submission_dir / "maintainer-summary.md").write_text(
        maintainer_summary(meta), encoding="utf-8"
    )
    ensure_submission_text(pr_dir, meta, "bugzilla-comment.txt", "Bugzilla comment")
    ensure_submission_text(pr_dir, meta, "mailing-list-cover.txt", "mailing-list cover")
    backports_dir = pr_dir / "backports"
    backports_dir.mkdir(parents=True, exist_ok=True)
    for branch, info in meta["backports"].items():
        branch_dir = backports_dir / branch
        branch_dir.mkdir(parents=True, exist_ok=True)
        write_json(branch_dir / "status.json", info)
        ensure_submission_text(pr_dir, meta, "bugzilla-comment.txt", "Bugzilla comment", branch)
        ensure_submission_text(pr_dir, meta, "mailing-list-cover.txt", "mailing-list cover", branch)
        (branch_dir / "summary.md").write_text(
            maintainer_summary(
                {
                    **meta,
                    "backports": {branch: info},
                }
            ),
            encoding="utf-8",
        )


def render_packets(paths: List[Path], regressions_only: bool) -> None:
    for pr_dir in paths:
        meta = load_status(pr_dir)
        if regressions_only and not meta["classification"]["regression"]:
            continue
        render_packet(meta)
        print(f"rendered packet for PR{meta['pr']}")
    matrix_rows = []
    for pr_dir in status_pr_dirs():
        meta = load_status(pr_dir)
        if regressions_only and not meta["classification"]["regression"]:
            continue
        matrix_rows.append(meta)
    write_backport_matrix(matrix_rows)


def write_backport_matrix(metadata_rows: List[Dict[str, Any]]) -> None:
    rows = sorted(metadata_rows, key=lambda x: x["pr"])
    md_lines = [
        "# Backport Matrix",
        "",
        "| PR | Regression | Fix status | Severity | gcc-15 | gcc-14 | gcc-13 |",
        "|----|------------|------------|----------|--------|--------|--------|",
    ]
    machine_rows = []
    for meta in rows:
        md_lines.append(
            "| {pr} | {reg} | {fix} | {sev} | {b15} | {b14} | {b13} |".format(
                pr=meta["pr"],
                reg="yes" if meta["classification"]["regression"] else "no",
                fix=meta["fix_status"],
                sev=meta["classification"]["severity"],
                b15=meta["backports"]["gcc-15"]["apply_mode"],
                b14=meta["backports"]["gcc-14"]["apply_mode"],
                b13=meta["backports"]["gcc-13"]["apply_mode"],
            )
        )
        machine_rows.append(
            {
                "pr": meta["pr"],
                "regression": meta["classification"]["regression"],
                "fix_status": meta["fix_status"],
                "severity": meta["classification"]["severity"],
                "backports": meta["backports"],
            }
        )
    (PR_ROOT / "backport-matrix.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    write_json(PR_ROOT / "backport-matrix.json", {"generated_at": timestamp(), "rows": machine_rows})


def scan_regressions(paths: List[Path]) -> None:
    metadata_rows = [load_status(path) for path in paths]
    write_backport_matrix([row for row in metadata_rows if row["classification"]["regression"]])
    print(f"wrote {PR_ROOT / 'backport-matrix.md'}")


def ensure_worktree(branch: str) -> Tuple[Path, Path]:
    info = ACTIVE_BRANCHES[branch]
    worktree = Path(info["worktree"])
    build_dir = Path(info["build"])
    if not worktree.exists():
        WORKTREE_ROOT.mkdir(parents=True, exist_ok=True)
        run(["git", "-C", str(GCC_DIR), "fetch", "upstream", info["ref"].split("/", 1)[1]])
        run(
            [
                "git",
                "-C",
                str(GCC_DIR),
                "worktree",
                "add",
                str(worktree),
                info["ref"],
            ]
        )
    return worktree, build_dir


def configure_branch_build(worktree: Path, build_dir: Path) -> None:
    if build_dir.exists() and (build_dir / "Makefile").exists():
        return
    build_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            str(worktree / "configure"),
            "--enable-languages=fortran",
            "--disable-multilib",
            "--disable-bootstrap",
            "CFLAGS=-Og -g",
            "CXXFLAGS=-Og -g",
        ],
        cwd=build_dir,
    )


def ensure_branch_compiler(build_dir: Path) -> None:
    gfortran = build_dir / "gcc" / "gfortran"
    f951 = build_dir / "gcc" / "f951"
    if gfortran.exists() and f951.exists():
        return
    run(["make", "-j32", "all-gcc"], cwd=build_dir, capture=False)


def build_branch_compiler(build_dir: Path) -> None:
    run(["make", "-j32", "all-gcc"], cwd=build_dir, capture=False)


def timestamp() -> str:
    return _dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def resolve_command_item(item: str, build_dir: Path) -> str:
    if item == "gcc-build/gcc/gfortran":
        return str(build_dir / "gcc" / "gfortran")
    if item == "gcc-build/gcc":
        return str(build_dir / "gcc")
    if item.startswith("pr/") or item.startswith("gcc-build/"):
        return str(ROOT / item)
    return item


def resolve_validation_command(spec: Dict[str, Any], build_dir: Path, key: str) -> List[str]:
    return [resolve_command_item(item, build_dir) for item in spec.get(key, [])]


def combined_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout or ''}\n{proc.stderr or ''}"


def merge_outputs(*procs: subprocess.CompletedProcess[str]) -> subprocess.CompletedProcess[str]:
    args = [proc.args for proc in procs if proc is not None]
    stdout = "\n".join(proc.stdout or "" for proc in procs if proc is not None)
    stderr = "\n".join(proc.stderr or "" for proc in procs if proc is not None)
    returncode = 0
    for proc in reversed(procs):
        if proc is not None:
            returncode = proc.returncode
            break
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def summarize_output(proc: subprocess.CompletedProcess[str], limit: int = 1200) -> str:
    output = combined_output(proc).strip()
    if not output:
        return "(no output)"
    if len(output) <= limit:
        return output
    return output[: limit - 3] + "..."


def execute_validation(spec: Dict[str, Any], build_dir: Path) -> subprocess.CompletedProcess[str]:
    env = spec.get("env", {})
    compile_proc = run(resolve_validation_command(spec, build_dir, "compile"), check=False, env=env)
    if spec.get("kind") != "run":
        return compile_proc
    if compile_proc.returncode != 0:
        return compile_proc
    run_proc = run(resolve_validation_command(spec, build_dir, "run"), check=False, env=env)
    return merge_outputs(compile_proc, run_proc)


def tests_from_patch(patch: Path) -> List[str]:
    matches = []
    marker = " b/gcc/testsuite/gfortran.dg/"
    for line in read_text(patch).splitlines():
        if marker not in line:
            continue
        rel = line.split(marker, 1)[1].strip()
        if rel and rel not in matches:
            matches.append(rel)
    return matches


def targeted_tests_for_meta(meta: Dict[str, Any]) -> List[str]:
    patch_name = meta["trunk"].get("patch")
    if patch_name:
        tests = tests_from_patch(PR_ROOT / str(meta["pr"]) / patch_name)
        if tests:
            return tests
    return [f"pr{meta['pr']}.f90"]


def reset_gfortran_results(build_dir: Path) -> None:
    testsuite_dir = build_dir / "gcc" / "testsuite" / "gfortran"
    for name in ("gfortran.sum", "gfortran.log"):
        path = testsuite_dir / name
        if path.exists():
            path.unlink()


def current_fail_xpass(build_dir: Path) -> List[str]:
    sum_path = build_dir / "gcc" / "testsuite" / "gfortran" / "gfortran.sum"
    if not sum_path.exists():
        return []
    return [
        line.strip()
        for line in read_text(sum_path).splitlines()
        if line.startswith("FAIL:") or line.startswith("XPASS:")
    ]


def run_targeted_tests(build_dir: Path, tests: List[str]) -> Tuple[str, str]:
    failures = []
    for test in tests:
        reset_gfortran_results(build_dir)
        run(
            ["make", "check-gfortran", f"RUNTESTFLAGS=dg.exp={test}"],
            cwd=build_dir / "gcc",
            capture=False,
            check=False,
        )
        bad = current_fail_xpass(build_dir)
        if bad:
            failures.append(f"{test}: {'; '.join(bad)}")
    if failures:
        return "fail", "targeted test regressions: " + " | ".join(failures)
    return "pass", f"targeted tests passed: {', '.join(tests)}"


def full_suite_cache_path(build_dir: Path) -> Path:
    return build_dir / ".workflow-gfortran-baseline.json"


def branch_ref_commit(worktree: Path, ref: str) -> str:
    return run(["git", "-C", str(worktree), "rev-parse", ref]).stdout.strip()


def load_or_compute_full_suite_baseline(branch: str, worktree: Path, build_dir: Path) -> List[str]:
    ref = ACTIVE_BRANCHES[branch]["ref"]
    commit = branch_ref_commit(worktree, ref)
    cache_path = full_suite_cache_path(build_dir)
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("ref") == ref and cached.get("commit") == commit:
            return cached.get("fail_xpass", [])
    run(["git", "-C", str(worktree), "reset", "--hard", ref], capture=False)
    build_branch_compiler(build_dir)
    reset_gfortran_results(build_dir)
    run(["make", "-j32", "-k", "check-gfortran"], cwd=build_dir / "gcc", capture=False)
    baseline = current_fail_xpass(build_dir)
    write_json(
        cache_path,
        {
            "branch": branch,
            "ref": ref,
            "commit": commit,
            "generated_at": timestamp(),
            "fail_xpass": baseline,
        },
    )
    return baseline


def run_full_suite(build_dir: Path, baseline: List[str]) -> Tuple[str, str]:
    reset_gfortran_results(build_dir)
    run(["make", "-j32", "-k", "check-gfortran"], cwd=build_dir / "gcc", capture=False)
    baseline_set = set(baseline)
    extra = [line for line in current_fail_xpass(build_dir) if line not in baseline_set]
    if extra:
        return "fail", "new FAIL/XPASS entries: " + " | ".join(extra[:10])
    return "pass", "no new FAIL/XPASS entries versus cached branch baseline"


def matches_expectation(proc: subprocess.CompletedProcess[str], expect: Dict[str, Any]) -> bool:
    output = combined_output(proc)
    exit_mode = expect.get("exit", "any")
    if exit_mode == "zero" and proc.returncode != 0:
        return False
    if exit_mode == "nonzero" and proc.returncode == 0:
        return False
    contains_any = expect.get("contains_any", [])
    if contains_any and not any(token in output for token in contains_any):
        return False
    for token in expect.get("contains_all", []):
        if token not in output:
            return False
    for token in expect.get("not_contains", []):
        if token in output:
            return False
    return True


def update_branch_state(
    pr_dir: Path,
    branch: str,
    *,
    reproduces: Optional[bool],
    apply_mode: str,
    notes: str,
    branch_commit: Optional[str] = None,
    branch_patch: Optional[str] = None,
    targeted_tests: str = "not-run",
    full_suite: str = "not-run",
) -> None:
    meta = load_status(pr_dir)
    candidate = None
    if meta["classification"]["regression"] and reproduces:
        candidate = True
    elif reproduces is False:
        candidate = False
    info = dict(meta["backports"][branch])
    info.update(
        {
            "reproduces": reproduces,
            "backport_candidate": candidate,
            "apply_mode": apply_mode,
            "branch_commit": branch_commit,
            "branch_patch": branch_patch,
            "targeted_tests": targeted_tests,
            "full_suite": full_suite,
            "notes": notes.strip(),
        }
    )
    meta["backports"][branch] = info
    meta["updated_at"] = timestamp()
    write_json(pr_dir / "status.json", meta)


def branch_check(paths: List[Path], branches: List[str], full_suite: bool) -> None:
    branch_context: Dict[str, Dict[str, Any]] = {}
    for branch in branches:
        worktree, build_dir = ensure_worktree(branch)
        configure_branch_build(worktree, build_dir)
        ensure_branch_compiler(build_dir)
        context: Dict[str, Any] = {"worktree": worktree, "build_dir": build_dir}
        if full_suite:
            context["baseline_fail_xpass"] = load_or_compute_full_suite_baseline(branch, worktree, build_dir)
        branch_context[branch] = context

    for pr_dir in paths:
        meta = load_status(pr_dir)
        if not meta["classification"]["regression"]:
            continue
        validation = meta["validation"]
        for branch in branches:
            worktree = branch_context[branch]["worktree"]
            build_dir = branch_context[branch]["build_dir"]
            ref = ACTIVE_BRANCHES[branch]["ref"]
            run(["git", "-C", str(worktree), "reset", "--hard", ref], capture=False)
            build_branch_compiler(build_dir)

            if validation.get("kind") == "special-env":
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=None,
                    apply_mode="needs-special-env",
                    notes=validation.get("reason", "requires environment not available in automated branch-check"),
                )
                render_packet(load_status(pr_dir))
                continue

            baseline_expect = validation.get("baseline")
            fixed_expect = validation.get("fixed")
            if not baseline_expect or not fixed_expect:
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=None,
                    apply_mode="invalid-validation-spec",
                    notes="validation spec must provide both baseline and fixed expectations",
                )
                render_packet(load_status(pr_dir))
                continue

            proc = execute_validation(validation, build_dir)
            reproduces = matches_expectation(proc, baseline_expect)

            if not reproduces:
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=False,
                    apply_mode="not-affected",
                    notes="baseline branch compiler does not match the recorded reproducer signature",
                )
                render_packet(load_status(pr_dir))
                continue

            if meta["fix_status"] not in {"patch-ready", "merged"} or not meta["trunk"]["commit"]:
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=True,
                    apply_mode="pending-trunk-fix",
                    notes="branch is affected but no trunk patch-ready or merged commit is recorded",
                )
                render_packet(load_status(pr_dir))
                continue

            temp_branch = f"backport/pr{meta['pr']}-{branch}"
            run(["git", "-C", str(worktree), "checkout", "-B", temp_branch, ref])
            cherry = run(
                [
                    "git",
                    "-C",
                    str(worktree),
                    "cherry-pick",
                    "-x",
                    meta["trunk"]["commit"],
                ],
                check=False,
            )
            if cherry.returncode != 0:
                run(["git", "-C", str(worktree), "cherry-pick", "--abort"], check=False)
                run(["git", "-C", str(worktree), "reset", "--hard", ref], capture=False)
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=True,
                    apply_mode="needs-adaptation",
                    notes=(cherry.stderr or cherry.stdout).strip()[:2000],
                )
                render_packet(load_status(pr_dir))
                continue

            try:
                build_branch_compiler(build_dir)
                fixed_proc = execute_validation(validation, build_dir)
                if not matches_expectation(fixed_proc, fixed_expect):
                    update_branch_state(
                        pr_dir,
                        branch,
                        reproduces=True,
                        apply_mode="fails-fixed-validation",
                        notes="branch patch applied, but fixed validation did not match expected signature:\n"
                        + summarize_output(fixed_proc),
                    )
                    render_packet(load_status(pr_dir))
                    continue

                branch_commit = run(
                    ["git", "-C", str(worktree), "rev-parse", "HEAD"]
                ).stdout.strip()
                patch_out = pr_dir / "backports" / branch
                patch_out.mkdir(parents=True, exist_ok=True)
                for old_patch in patch_out.glob("0001-*.patch"):
                    old_patch.unlink()
                run(
                    [
                        "git",
                        "-C",
                        str(worktree),
                        "format-patch",
                        "-1",
                        "HEAD",
                        "-o",
                        str(patch_out),
                    ]
                )
                branch_patch = sorted(patch_out.glob("0001-*.patch"))[0]

                targeted_state, targeted_note = run_targeted_tests(build_dir, targeted_tests_for_meta(meta))
                if targeted_state != "pass":
                    update_branch_state(
                        pr_dir,
                        branch,
                        reproduces=True,
                        apply_mode="fails-targeted-tests",
                        notes=targeted_note,
                        branch_commit=branch_commit,
                        branch_patch=str(branch_patch.relative_to(pr_dir)),
                        targeted_tests=targeted_state,
                        full_suite="not-run",
                    )
                    render_packet(load_status(pr_dir))
                    continue

                full_state = "not-run"
                note = targeted_note
                apply_mode = "validated-targeted"
                if full_suite:
                    full_state, full_note = run_full_suite(
                        build_dir, branch_context[branch]["baseline_fail_xpass"]
                    )
                    note = targeted_note + "; " + full_note
                    apply_mode = "ready" if full_state == "pass" else "fails-full-suite"

                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=True,
                    apply_mode=apply_mode,
                    notes=note,
                    branch_commit=branch_commit,
                    branch_patch=str(branch_patch.relative_to(pr_dir)),
                    targeted_tests=targeted_state,
                    full_suite=full_state,
                )
                render_packet(load_status(pr_dir))
            finally:
                run(["git", "-C", str(worktree), "reset", "--hard", ref], capture=False)
    scan_regressions(paths)


def selected_patch(meta: Dict[str, Any], branch: str) -> Path:
    pr_dir = PR_ROOT / str(meta["pr"])
    if branch == "trunk":
        patch = meta["trunk"].get("patch")
        if not patch:
            raise WorkflowError(f"PR{meta['pr']} has no trunk patch recorded")
        return pr_dir / patch
    branch_patch = meta["backports"][branch].get("branch_patch")
    if not branch_patch:
        raise WorkflowError(f"PR{meta['pr']} has no {branch} patch recorded")
    return pr_dir / branch_patch


def submit_bugzilla(pr: int, branch: str, execute: bool) -> None:
    pr_dir = PR_ROOT / str(pr)
    meta = load_status(pr_dir)
    patch = selected_patch(meta, branch)
    comment_path, comment = load_submission_text(
        pr_dir, meta, "bugzilla-comment.txt", "Bugzilla comment", branch
    )
    cmd = [
        str(ROOT / "scripts" / "gcc-bugzilla.sh"),
        "attach",
        str(meta["bugzilla"]["id"]),
        str(patch),
        patch.name,
        comment,
    ]
    if execute:
        run(cmd, capture=False, env={"GCC_BUGZILLA_ASSUME_YES": "1"})
    else:
        print("dry-run:")
        print(" ".join(shlex.quote(x) for x in cmd))
        print(f"using comment from: {comment_path.relative_to(ROOT)}")
        print(comment)


def submit_mail(pr: int, branch: str, execute: bool) -> None:
    pr_dir = PR_ROOT / str(pr)
    meta = load_status(pr_dir)
    patch = selected_patch(meta, branch)
    cover_path, cover = load_submission_text(
        pr_dir, meta, "mailing-list-cover.txt", "mailing-list cover", branch
    )
    cmd = [str(ROOT / "scripts" / "gcc-send-patch.sh")]
    if not execute:
        cmd.append("--dry-run")
    cmd.append(str(patch))
    print(f"using cover from: {cover_path.relative_to(ROOT)}")
    print(cover)
    run(cmd, capture=False, env={"GCC_SEND_PATCH_ASSUME_YES": "1"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync-metadata", help="Create or update pr/<n>/status.json")
    p_sync.add_argument("prs", nargs="*", help="PR numbers to sync; default all")
    p_sync.add_argument("--all", action="store_true", help="Sync all PR directories")
    p_sync.add_argument("--refresh-bugzilla", action="store_true", help="Refresh public Bugzilla metadata via XML-RPC")

    p_scan = sub.add_parser("scan-regressions", help="Write the top-level regression backport matrix")
    p_scan.add_argument("prs", nargs="*", help="Optional PR subset")

    p_render = sub.add_parser("render-packet", help="Render structured docs and submission packets")
    p_render.add_argument("prs", nargs="*", help="Optional PR subset")
    p_render.add_argument("--all", action="store_true", help="Render for all PR directories")
    p_render.add_argument("--regressions", action="store_true", help="Render only regression PRs")

    p_branch = sub.add_parser("branch-check", help="Run branch applicability checks for regression PRs")
    p_branch.add_argument("prs", nargs="*", help="Optional PR subset")
    p_branch.add_argument(
        "--branches",
        default="gcc-15,gcc-14,gcc-13",
        help="Comma-separated release branches to check",
    )
    p_branch.add_argument(
        "--no-full-suite",
        action="store_true",
        help="Skip full check-gfortran on release branches",
    )

    p_bz = sub.add_parser("submit-bugzilla", help="Submit a generated packet to Bugzilla")
    p_bz.add_argument("pr", type=int)
    p_bz.add_argument("--branch", default="trunk")
    p_bz.add_argument("--execute", action="store_true")

    p_mail = sub.add_parser("submit-mail", help="Submit a generated packet to gcc-patches")
    p_mail.add_argument("pr", type=int)
    p_mail.add_argument("--branch", default="trunk")
    p_mail.add_argument("--execute", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cmd == "sync-metadata":
        paths = pr_dirs(None if args.all or not args.prs else args.prs)
        sync_metadata(paths, args.refresh_bugzilla)
        return 0
    if args.cmd == "scan-regressions":
        scan_regressions(status_pr_dirs(args.prs or None))
        return 0
    if args.cmd == "render-packet":
        paths = status_pr_dirs(None if args.all or not args.prs else args.prs)
        render_packets(paths, regressions_only=args.regressions)
        return 0
    if args.cmd == "branch-check":
        branches = [item.strip() for item in args.branches.split(",") if item.strip()]
        unknown = [branch for branch in branches if branch not in ACTIVE_BRANCHES]
        if unknown:
            raise WorkflowError(f"unknown branches: {', '.join(unknown)}")
        branch_check(status_pr_dirs(args.prs or None), branches, full_suite=not args.no_full_suite)
        return 0
    if args.cmd == "submit-bugzilla":
        submit_bugzilla(args.pr, args.branch, args.execute)
        return 0
    if args.cmd == "submit-mail":
        submit_mail(args.pr, args.branch, args.execute)
        return 0
    raise WorkflowError(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
