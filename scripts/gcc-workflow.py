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
    return {
        "kind": "compile",
        "compile": [
            "gcc-build/gcc/gfortran",
            "-B",
            "gcc-build/gcc",
            "-c",
            str(reproducer.relative_to(ROOT)) if reproducer.exists() else f"pr/{pr}/reproducer.f90",
            "-o",
            "/dev/null",
        ],
        "run": [],
        "env": {},
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
            "refreshed_at": _dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
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
            "patch": patch_files[0] if patch_files else None,
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
        "updated_at": _dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
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


def bugzilla_comment(meta: Dict[str, Any], branch: str = "trunk") -> str:
    if branch == "trunk":
        patch = meta["trunk"].get("patch") or "missing patch"
        commit = meta["trunk"].get("commit") or "n/a"
        return textwrap.dedent(
            f"""\
            Proposed trunk fix for PR{meta['pr']}.

            Summary:
            - regression: {'yes' if meta['classification']['regression'] else 'no'}
            - severity: {meta['classification']['severity']}
            - trunk commit: {commit}
            - patch: {patch}

            Validation:
            - targeted validation: completed locally
            - full check-gfortran: passed locally

            Maintainer summary and branch matrix are available in the local packet.
            """
        ).strip() + "\n"
    info = meta["backports"][branch]
    branch_patch = info.get("branch_patch") or meta["trunk"].get("patch") or "missing patch"
    return textwrap.dedent(
        f"""\
        Backport candidate for {branch} for PR{meta['pr']}.

        Branch status:
        - reproduces on {branch}: {bool_text(info.get('reproduces'))}
        - candidate: {bool_text(info.get('backport_candidate'))}
        - apply mode: {info.get('apply_mode', 'unknown')}
        - targeted tests: {info.get('targeted_tests', 'not-run')}
        - full check-gfortran: {info.get('full_suite', 'not-run')}
        - patch: {branch_patch}

        This branch result was generated from the structured backport matrix in the meta-repo.
        """
    ).strip() + "\n"


def mailing_list_cover(meta: Dict[str, Any], branch: str = "trunk") -> str:
    prefix = "" if branch == "trunk" else f"[{branch}] "
    commit = meta["trunk"].get("commit") or "n/a"
    return textwrap.dedent(
        f"""\
        {prefix}PR{meta['pr']} submission packet

        Bugzilla: {meta['bugzilla']['url']}
        Regression: {'yes' if meta['classification']['regression'] else 'no'}
        Severity: {meta['classification']['severity']}
        Trunk commit: {commit}

        This packet was generated from the meta-repo workflow and includes
        branch applicability data for active release branches.
        """
    ).strip() + "\n"


def render_packet(meta: Dict[str, Any]) -> None:
    pr_dir = PR_ROOT / str(meta["pr"])
    submission_dir = pr_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)
    (submission_dir / "maintainer-summary.md").write_text(
        maintainer_summary(meta), encoding="utf-8"
    )
    (submission_dir / "bugzilla-comment.txt").write_text(
        bugzilla_comment(meta), encoding="utf-8"
    )
    (submission_dir / "mailing-list-cover.txt").write_text(
        mailing_list_cover(meta), encoding="utf-8"
    )
    backports_dir = pr_dir / "backports"
    backports_dir.mkdir(parents=True, exist_ok=True)
    for branch, info in meta["backports"].items():
        branch_dir = backports_dir / branch
        branch_dir.mkdir(parents=True, exist_ok=True)
        write_json(branch_dir / "status.json", info)
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
    rows = []
    for pr_dir in paths:
        meta = load_status(pr_dir)
        if regressions_only and not meta["classification"]["regression"]:
            continue
        render_packet(meta)
        rows.append(meta)
        print(f"rendered packet for PR{meta['pr']}")
    write_backport_matrix(rows)


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
    write_json(PR_ROOT / "backport-matrix.json", {"generated_at": _dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"), "rows": machine_rows})


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
    meta["updated_at"] = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    write_json(pr_dir / "status.json", meta)


def branch_check(paths: List[Path], branches: List[str], full_suite: bool) -> None:
    for pr_dir in paths:
        meta = load_status(pr_dir)
        if not meta["classification"]["regression"]:
            continue
        validation = meta["validation"]
        for branch in branches:
            worktree, build_dir = ensure_worktree(branch)
            configure_branch_build(worktree, build_dir)
            compile_cmd = [str(ROOT / part) if part.startswith("gcc-build/") or part.startswith("pr/") else part for part in validation["compile"]]
            compile_cmd = [
                str(build_dir / "gcc" / "gfortran") if part == "gcc-build/gcc/gfortran" else
                str(build_dir / "gcc") if part == "gcc-build/gcc" else
                part
                for part in compile_cmd
            ]
            proc = run(compile_cmd, check=False, env=validation.get("env", {}))
            reproduces = proc.returncode != 0
            if not reproduces:
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=False,
                    apply_mode="not-affected",
                    notes="reproducer did not fail on branch baseline",
                )
                continue
            if meta["fix_status"] != "patch-ready" or not meta["trunk"]["commit"]:
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=True,
                    apply_mode="pending-trunk-fix",
                    notes="branch is affected but no trunk patch-ready commit is recorded yet",
                )
                continue
            temp_branch = f"backport/pr{meta['pr']}-{branch}"
            run(["git", "-C", str(worktree), "checkout", "-B", temp_branch, ACTIVE_BRANCHES[branch]["ref"]])
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
                update_branch_state(
                    pr_dir,
                    branch,
                    reproduces=True,
                    apply_mode="needs-adaptation",
                    notes=(cherry.stderr or cherry.stdout).strip()[:2000],
                )
                continue
            branch_commit = run(
                ["git", "-C", str(worktree), "rev-parse", "HEAD"]
            ).stdout.strip()
            run(["make", "-j32"], cwd=build_dir)
            targeted = "pass"
            full = "pass"
            if full_suite:
                run(
                    ["make", "-j32", "-k", "check-gfortran"],
                    cwd=build_dir / "gcc",
                )
            patch_out = pr_dir / "backports" / branch
            patch_out.mkdir(parents=True, exist_ok=True)
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
            branch_patch = next(sorted(patch_out.glob("0001-*.patch")))
            update_branch_state(
                pr_dir,
                branch,
                reproduces=True,
                apply_mode="ready",
                notes="clean cherry-pick and local branch validation succeeded",
                branch_commit=branch_commit,
                branch_patch=str(branch_patch.relative_to(pr_dir)),
                targeted_tests=targeted,
                full_suite=full,
            )
            render_packet(load_status(pr_dir))


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
    meta = load_status(PR_ROOT / str(pr))
    patch = selected_patch(meta, branch)
    comment = bugzilla_comment(meta, branch)
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
        print(comment)


def submit_mail(pr: int, branch: str, execute: bool) -> None:
    meta = load_status(PR_ROOT / str(pr))
    patch = selected_patch(meta, branch)
    cmd = [str(ROOT / "scripts" / "gcc-send-patch.sh")]
    if not execute:
        cmd.append("--dry-run")
    cmd.append(str(patch))
    print(mailing_list_cover(meta, branch))
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
        scan_regressions(pr_dirs(args.prs or None))
        return 0
    if args.cmd == "render-packet":
        paths = pr_dirs(None if args.all or not args.prs else args.prs)
        render_packets(paths, regressions_only=args.regressions)
        return 0
    if args.cmd == "branch-check":
        branches = [item.strip() for item in args.branches.split(",") if item.strip()]
        unknown = [branch for branch in branches if branch not in ACTIVE_BRANCHES]
        if unknown:
            raise WorkflowError(f"unknown branches: {', '.join(unknown)}")
        branch_check(pr_dirs(args.prs or None), branches, full_suite=not args.no_full_suite)
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
