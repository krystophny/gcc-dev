#!/usr/bin/env python3
"""Reverse-provenance scanner: upstream files that carry GCC code without
proper attribution back to GCC/FSF.

The source-level scanner (scan_sources.py) looks for GCC files that copied
from an upstream without crediting. This one flips the direction: take the
same (gcc_file, upstream_file) pairs and check whether the UPSTREAM copy
carries the required attribution to GCC when the evidence suggests GCC was
the donor.

Inputs:
  - A scan_sources.py JSON report (default: /tmp/source-provenance-all-cpd.json)
  - Fetched corpus under corpusbin/src/ (read to classify upstream headers)
  - Optional: gcc/ tree for git-log based date cross-check (skipped when absent)

For every (path, match) pair with density + shingle above configurable floors
we inspect the upstream header for GCC/FSF attribution markers. If the header
carries none, the pair is flagged as a downstream-provenance candidate. A
best-effort directionality check compares the GCC introduction date with the
upstream introduction date of the matched file; if GCC predates upstream we
upgrade severity from "medium" to "high" and attach the dates as evidence.

This script is diagnostic. It does not file issues on its own. Review the
report and use file_findings-style workflow to open issues under the
`provenance:downstream` label.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_ROOT = REPO_ROOT / "corpusbin" / "src"
GCC_ROOT = REPO_ROOT / "gcc"

# Markers that count as "acknowledges GCC/FSF/Runtime Library Exception".
# A file that mentions any of these is NOT silent w.r.t. GCC provenance.
GCC_ATTRIBUTION_MARKERS = (
    re.compile(r"\bGCC\b"),
    re.compile(r"GNU\s+Compiler\s+Collection", re.IGNORECASE),
    re.compile(r"Free\s+Software\s+Foundation", re.IGNORECASE),
    re.compile(r"Runtime\s+Library\s+Exception", re.IGNORECASE),
    re.compile(r"\blibgcc\b"),
    re.compile(r"\blibstdc\+\+\b", re.IGNORECASE),
    re.compile(r"\blibgomp\b"),
    re.compile(r"\blibgfortran\b"),
    re.compile(r"\blibobjc\b"),
    re.compile(r"\blibquadmath\b"),
    re.compile(r"\blibiberty\b"),
    re.compile(r"\blibsupc\+\+", re.IGNORECASE),
    re.compile(r"kept\s+in\s+sync\s+with\s+libgcc", re.IGNORECASE),
    re.compile(r"gcc\.gnu\.org", re.IGNORECASE),
    re.compile(r"sourceware\.org/gcc", re.IGNORECASE),
    # LGPL/GPL v2+ / v3+ headers on their own are NOT enough — the file
    # could be from gnulib or glibc. We require a specific GCC-project
    # mention.
)

# If the upstream has NO Free Software Foundation copyright at all, it is
# almost certainly not a GCC-sourced file even when code matches. This is
# usually the case for BSD-licensed copies where the upstream is the
# canonical source and GCC imported it. We skip such pairs.
FSF_COPYRIGHT_RE = re.compile(r"Free\s+Software\s+Foundation", re.IGNORECASE)

# Tracker URLs per upstream project. First entry is the preferred issue
# tracker URL; the second entry is a human label for the write-up.
TRACKERS = {
    "musl": ("https://www.openwall.com/lists/musl/", "musl mailing list"),
    "freebsd-libc": ("https://bugs.freebsd.org/bugzilla/", "FreeBSD Bugzilla"),
    "netbsd-libc": ("https://gnats.netbsd.org/", "NetBSD GNATS"),
    "openbsd-libc": ("https://www.openbsd.org/report.html", "OpenBSD bug reporting"),
    "bionic": ("https://issuetracker.google.com/issues/new?component=192727", "AOSP Issue Tracker"),
    "apple-libc": ("https://feedbackassistant.apple.com/", "Apple Feedback Assistant"),
    "apple-libplatform": ("https://feedbackassistant.apple.com/", "Apple Feedback Assistant"),
    "illumos": ("https://www.illumos.org/issues", "illumos issue tracker"),
    "netlib-gdtoa": ("https://github.com/jwiegley/gdtoa/issues", "gdtoa GitHub issues"),
    "linux-kernel-lib": ("https://bugzilla.kernel.org/", "kernel.org Bugzilla"),
    "golang-stdlib": ("https://github.com/golang/go/issues", "golang/go issues"),
    "cpython": ("https://github.com/python/cpython/issues", "python/cpython issues"),
    "abseil-cpp": ("https://github.com/abseil/abseil-cpp/issues", "abseil-cpp issues"),
    "folly": ("https://github.com/facebook/folly/issues", "facebook/folly issues"),
    "rapidjson": ("https://github.com/Tencent/rapidjson/issues", "Tencent/rapidjson issues"),
    "simdjson": ("https://github.com/simdjson/simdjson/issues", "simdjson/simdjson issues"),
    "protobuf": ("https://github.com/protocolbuffers/protobuf/issues", "protocolbuffers/protobuf issues"),
    "openssl": ("https://github.com/openssl/openssl/issues", "openssl/openssl issues"),
    "nss": ("https://bugzilla.mozilla.org/enter_bug.cgi?product=NSS", "Mozilla NSS Bugzilla"),
    "libsodium": ("https://github.com/jedisct1/libsodium/issues", "jedisct1/libsodium issues"),
    "libxml2": ("https://gitlab.gnome.org/GNOME/libxml2/-/issues", "GNOME libxml2 issues"),
    "libcurl": ("https://github.com/curl/curl/issues", "curl/curl issues"),
    "libunistring": ("https://savannah.gnu.org/bugs/?group=libunistring", "libunistring Savannah"),
    "icu": ("https://unicode-org.atlassian.net/projects/ICU", "Unicode ICU Jira"),
    "pcre2": ("https://github.com/PCRE2Project/pcre2/issues", "PCRE2Project/pcre2 issues"),
    "jemalloc": ("https://github.com/jemalloc/jemalloc/issues", "jemalloc/jemalloc issues"),
    "mimalloc": ("https://github.com/microsoft/mimalloc/issues", "microsoft/mimalloc issues"),
    "gperftools": ("https://github.com/gperftools/gperftools/issues", "gperftools issues"),
    "xxhash": ("https://github.com/Cyan4973/xxHash/issues", "Cyan4973/xxHash issues"),
    "lz4": ("https://github.com/lz4/lz4/issues", "lz4/lz4 issues"),
    "snappy": ("https://github.com/google/snappy/issues", "google/snappy issues"),
    "brotli": ("https://github.com/google/brotli/issues", "google/brotli issues"),
    "zlib": ("https://github.com/madler/zlib/issues", "madler/zlib issues"),
    "zlib-ng": ("https://github.com/zlib-ng/zlib-ng/issues", "zlib-ng/zlib-ng issues"),
    "pcg-c": ("https://github.com/imneme/pcg-c/issues", "imneme/pcg-c issues"),
    "boost-math": ("https://github.com/boostorg/math/issues", "boostorg/math issues"),
    "boost-multiprecision": ("https://github.com/boostorg/multiprecision/issues", "boostorg/multiprecision issues"),
    "boost-unordered": ("https://github.com/boostorg/unordered/issues", "boostorg/unordered issues"),
    "boost-container": ("https://github.com/boostorg/container/issues", "boostorg/container issues"),
    "boost-algorithm": ("https://github.com/boostorg/algorithm/issues", "boostorg/algorithm issues"),
    "boost-charconv": ("https://github.com/boostorg/charconv/issues", "boostorg/charconv issues"),
    "eigen": ("https://gitlab.com/libeigen/eigen/-/issues", "libeigen/eigen issues"),
    "sleef": ("https://github.com/shibatch/sleef/issues", "shibatch/sleef issues"),
    "postgresql": ("https://www.postgresql.org/account/submitbug/", "PostgreSQL bug submission"),
    "sqlite": ("https://sqlite.org/forum/", "SQLite forum"),
    "chromium-base": ("https://bugs.chromium.org/p/chromium/issues/list", "Chromium bug tracker"),
    "v8": ("https://bugs.chromium.org/p/v8/issues/list", "V8 bug tracker"),
    "swift-corelibs-libc": ("https://github.com/apple/swift/issues", "apple/swift issues"),
    "bzip2": ("https://gitlab.com/bzip2/bzip2/-/issues", "bzip2 issues"),
    "zstd": ("https://github.com/facebook/zstd/issues", "facebook/zstd issues"),
    "openblas": ("https://github.com/OpenMathLib/OpenBLAS/issues", "OpenMathLib/OpenBLAS issues"),
    "sollve_vv": ("https://github.com/SOLLVE/sollve_vv/issues", "SOLLVE/sollve_vv issues"),
    "openmp-examples": ("https://github.com/OpenMP/Examples/issues", "OpenMP/Examples issues"),
    "lapack": ("https://github.com/Reference-LAPACK/lapack/issues", "Reference-LAPACK/lapack issues"),
    "llvm-project": ("https://github.com/llvm/llvm-project/issues", "llvm/llvm-project issues"),
    "gofrontend": ("https://github.com/golang/gofrontend/issues", "golang/gofrontend issues"),
    "dmd-druntime": ("https://github.com/dlang/dmd/issues", "dlang/dmd issues"),
    "rustc": ("https://github.com/rust-lang/rust/issues", "rust-lang/rust issues"),
    "newlib-cygwin": ("https://sourceware.org/bugzilla/enter_bug.cgi?product=newlib", "newlib Bugzilla"),
    "gnulib": ("https://lists.gnu.org/mailman/listinfo/bug-gnulib", "bug-gnulib mailing list"),
    "binutils-gdb": ("https://sourceware.org/bugzilla/enter_bug.cgi?product=binutils", "binutils Bugzilla"),
    "gettext": ("https://savannah.gnu.org/bugs/?group=gettext", "gettext Savannah"),
    "ulfjack-ryu": ("https://github.com/ulfjack/ryu/issues", "ulfjack/ryu issues"),
    "fmtlib": ("https://github.com/fmtlib/fmt/issues", "fmtlib/fmt issues"),
    "a68g": ("https://github.com/dvirtz/Algol68G-mirror/issues", "Algol68G issues"),
    "libatomic_ops": ("https://github.com/ivmai/libatomic_ops/issues", "ivmai/libatomic_ops issues"),
    "gnucobol": ("https://github.com/OCamlPro/gnucobol/issues", "OCamlPro/gnucobol issues"),
    "gmp": ("https://gmplib.org/list-archives/gmp-bugs/", "gmp-bugs mailing list"),
    "glibc": ("https://sourceware.org/bugzilla/enter_bug.cgi?product=glibc", "glibc Bugzilla"),
    "arm-optimized-routines": ("https://github.com/ARM-software/optimized-routines/issues", "ARM-software/optimized-routines issues"),
    "openlibm": ("https://github.com/JuliaMath/openlibm/issues", "JuliaMath/openlibm issues"),
    "picolibc": ("https://github.com/picolibc/picolibc/issues", "picolibc/picolibc issues"),
    "microsoft-stl": ("https://github.com/microsoft/STL/issues", "microsoft/STL issues"),
    "fast-float": ("https://github.com/fastfloat/fast_float/issues", "fastfloat/fast_float issues"),
    "double-conversion": ("https://github.com/google/double-conversion/issues", "google/double-conversion issues"),
    "dragonbox": ("https://github.com/jk-jeon/dragonbox/issues", "jk-jeon/dragonbox issues"),
    "highway": ("https://github.com/google/highway/issues", "google/highway issues"),
    "onetbb": ("https://github.com/oneapi-src/oneTBB/issues", "oneapi-src/oneTBB issues"),
    "libunwind-nongnu": ("https://github.com/libunwind/libunwind/issues", "libunwind/libunwind issues"),
    "libdispatch": ("https://github.com/apple/swift-corelibs-libdispatch/issues", "swift-corelibs-libdispatch issues"),
    "dlang-phobos": ("https://github.com/dlang/phobos/issues", "dlang/phobos issues"),
    "apple-objc4": ("https://feedbackassistant.apple.com/", "Apple Feedback Assistant"),
    "zig-stdlib": ("https://github.com/ziglang/zig/issues", "ziglang/zig issues"),
    "microsoft-gsl": ("https://github.com/microsoft/GSL/issues", "microsoft/GSL issues"),
    "parallel-hashmap": ("https://github.com/greg7mdp/parallel-hashmap/issues", "greg7mdp/parallel-hashmap issues"),
    "unordered-dense": ("https://github.com/martinus/unordered_dense/issues", "martinus/unordered_dense issues"),
    "onedpl": ("https://github.com/oneapi-src/oneDPL/issues", "oneapi-src/oneDPL issues"),
    "concurrencpp": ("https://github.com/David-Haim/concurrencpp/issues", "David-Haim/concurrencpp issues"),
    "taskflow": ("https://github.com/taskflow/taskflow/issues", "taskflow/taskflow issues"),
    "quickjs-ng": ("https://github.com/quickjs-ng/quickjs/issues", "quickjs-ng/quickjs issues"),
    "xsimd": ("https://github.com/xtensor-stack/xsimd/issues", "xtensor-stack/xsimd issues"),
    "nvidia-cccl": ("https://github.com/NVIDIA/cccl/issues", "NVIDIA/cccl issues"),
    "seastar": ("https://github.com/scylladb/seastar/issues", "scylladb/seastar issues"),
    "openacc-vv": ("https://github.com/OACC-Validation/OpenACCV-V/issues", "OpenACCV-V issues"),
    "ldc-phobos": ("https://github.com/ldc-developers/phobos/issues", "ldc-developers/phobos issues"),
    "wangle": ("https://github.com/facebook/wangle/issues", "facebook/wangle issues"),
}


@dataclass
class DownstreamFinding:
    gcc_path: str
    upstream_project: str
    upstream_relpath: str
    winnow_density: float
    shingle_jaccard: float
    line_jaccard: float
    longest_run: int
    tlsh_distance: int
    upstream_has_gcc_marker: bool
    upstream_header_excerpt: str
    gcc_intro_date: str = ""
    upstream_intro_date: str = ""
    gcc_intro_commit: str = ""
    upstream_intro_commit: str = ""
    directionality: str = "unknown"  # "gcc_first" | "upstream_first" | "contemporaneous" | "unknown"
    severity: str = "medium"
    tracker_url: str = ""
    tracker_label: str = ""
    note: str = ""


def read_header(path: Path, lines: int = 40) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return "".join(handle.readline() for _ in range(lines))
    except OSError:
        return ""


def upstream_has_gcc_attribution(header: str) -> bool:
    return any(pat.search(header) for pat in GCC_ATTRIBUTION_MARKERS)


def gcc_has_fsf(header: str) -> bool:
    return bool(FSF_COPYRIGHT_RE.search(header))


def _git_has_history(repo: Path) -> bool:
    """Return True when this clone carries more than a shallow single commit.

    The corpus clones under corpusbin/src/* are all --depth=1, so their
    git log is not a reliable provenance source. We recognise that via
    the presence of .git/shallow and a commit count of 1. When that is
    the case we refuse to claim introduction dates."""
    if not (repo / ".git").exists():
        return False
    shallow = repo / ".git" / "shallow"
    if shallow.exists():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return False
    try:
        return int((result.stdout or "0").strip()) > 1
    except ValueError:
        return False


def git_first_commit_date(repo: Path, rel: str) -> tuple[str, str]:
    """Return (YYYY-MM-DD, short-sha) for the introduction commit or ("","")."""
    if not _git_has_history(repo):
        return ("", "")
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "log", "--diff-filter=A", "--reverse",
             "--format=%h %ad", "--date=short", "--", rel],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return ("", "")
    line = (result.stdout.splitlines() or [""])[0].strip()
    if not line:
        return ("", "")
    parts = line.split(None, 1)
    if len(parts) < 2:
        return ("", "")
    sha, date = parts
    return (date, sha)


def classify(df: DownstreamFinding) -> str:
    """Severity of the reverse-provenance finding.

    The ONLY way to claim gcc_first with high confidence from within this
    scanner is to have real git history on the upstream clone (which the
    shallow corpus clones do not provide). So we leave severity based on
    content similarity alone and defer directionality to human review.
    """
    d = df.winnow_density
    s = df.shingle_jaccard
    if d >= 0.80 and s >= 0.70:
        base = "high"
    elif d >= 0.60 and s >= 0.45:
        base = "medium"
    elif d >= 0.40 and s >= 0.30:
        base = "low"
    else:
        base = "low"
    # If we DO have real upstream history and GCC is demonstrably earlier,
    # bump one step. Never reach "critical" from the scanner alone.
    if df.directionality == "gcc_first":
        return {"low": "medium", "medium": "high", "high": "high"}[base]
    return base


def check_directionality(gcc_path: str, corpus_rel: Path) -> tuple[str, str, str, str, str]:
    """Return (direction, gcc_date, gcc_sha, up_date, up_sha). Best effort."""
    gcc_rel = gcc_path[len("gcc/"):] if gcc_path.startswith("gcc/") else gcc_path
    gcc_date, gcc_sha = git_first_commit_date(GCC_ROOT, gcc_rel)
    project, _, sub = str(corpus_rel).partition("/")
    up_date, up_sha = git_first_commit_date(CORPUS_ROOT / project, sub)
    if gcc_date and up_date:
        if gcc_date < up_date:
            direction = "gcc_first"
        elif gcc_date > up_date:
            direction = "upstream_first"
        else:
            direction = "contemporaneous"
    else:
        direction = "unknown"
    return direction, gcc_date, gcc_sha, up_date, up_sha


def iterate_pairs(report: dict, density_floor: float, shingle_floor: float):
    for f in report.get("findings", []):
        gcc_path = f.get("path")
        if not gcc_path:
            continue
        for m in f.get("matches") or []:
            d = float(m.get("winnow_density", 0.0))
            s = float(m.get("shingle_jaccard", 0.0))
            if d < density_floor and s < shingle_floor:
                continue
            yield f, m


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?",
                        default=str(Path("/tmp/source-provenance-all-cpd.json")),
                        help="scan_sources.py JSON output to ingest")
    parser.add_argument("--density-floor", type=float, default=0.40)
    parser.add_argument("--shingle-floor", type=float, default=0.30)
    parser.add_argument("--skip-git", action="store_true",
                        help="Do not run git log for introduction dates")
    parser.add_argument("--require-gcc-fsf", action="store_true",
                        help="Only consider pairs where the GCC file carries an FSF copyright")
    parser.add_argument("--json", help="Write report to this path")
    parser.add_argument("--min-severity", default="medium",
                        choices=("low", "medium", "high", "critical"))
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"report not found: {report_path}", file=sys.stderr)
        return 1
    report = json.loads(report_path.read_text(encoding="utf-8"))

    findings: list[DownstreamFinding] = []
    seen: set[tuple[str, str, str]] = set()

    rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    min_rank = rank[args.min_severity]

    for f, m in iterate_pairs(report, args.density_floor, args.shingle_floor):
        gcc_path = f["path"]
        project = m["project"]
        rel = m["relpath"]
        key = (gcc_path, project, rel)
        if key in seen:
            continue
        seen.add(key)

        corpus_path = CORPUS_ROOT / project / rel
        gcc_full = REPO_ROOT / gcc_path
        if not corpus_path.exists() or not gcc_full.exists():
            continue

        up_header = read_header(corpus_path)
        gcc_header = read_header(gcc_full)

        if args.require_gcc_fsf and not gcc_has_fsf(gcc_header):
            continue

        if upstream_has_gcc_attribution(up_header):
            # Upstream credits GCC/FSF somewhere in the header, move on.
            continue

        if args.skip_git:
            direction, gcc_date, gcc_sha, up_date, up_sha = "unknown", "", "", "", ""
        else:
            direction, gcc_date, gcc_sha, up_date, up_sha = check_directionality(
                gcc_path, Path(project) / rel
            )

        df = DownstreamFinding(
            gcc_path=gcc_path,
            upstream_project=project,
            upstream_relpath=rel,
            winnow_density=float(m.get("winnow_density", 0.0)),
            shingle_jaccard=float(m.get("shingle_jaccard", 0.0)),
            line_jaccard=float(m.get("line_jaccard", 0.0)),
            longest_run=int(m.get("longest_run", 0)),
            tlsh_distance=int(m.get("tlsh_distance", -1)),
            upstream_has_gcc_marker=False,
            upstream_header_excerpt="\n".join(
                line.rstrip() for line in up_header.splitlines()[:10]
            ),
            gcc_intro_date=gcc_date,
            gcc_intro_commit=gcc_sha,
            upstream_intro_date=up_date,
            upstream_intro_commit=up_sha,
            directionality=direction,
        )
        df.severity = classify(df)
        tracker = TRACKERS.get(project)
        if tracker:
            df.tracker_url, df.tracker_label = tracker
        findings.append(df)

    findings.sort(key=lambda d: (-rank.get(d.severity, 0), -d.winnow_density, d.gcc_path))
    findings = [d for d in findings if rank[d.severity] >= min_rank]

    # Text report
    print(f"downstream findings kept: {len(findings)}")
    for i, d in enumerate(findings[:60], 1):
        print(f"{i:02d}. {d.severity:8s} dir={d.directionality:15s} "
              f"{d.upstream_project}/{d.upstream_relpath}  <-  {d.gcc_path}")
        print(f"    winnow={d.winnow_density:.3f} shingle={d.shingle_jaccard:.3f} "
              f"line={d.line_jaccard:.3f}")
        if d.gcc_intro_date or d.upstream_intro_date:
            print(f"    gcc_date={d.gcc_intro_date}@{d.gcc_intro_commit or '?'}"
                  f"  up_date={d.upstream_intro_date}@{d.upstream_intro_commit or '?'}")
        if d.tracker_url:
            print(f"    tracker: {d.tracker_label} ({d.tracker_url})")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {"count": len(findings),
                 "findings": [asdict(d) for d in findings]},
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"json: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
