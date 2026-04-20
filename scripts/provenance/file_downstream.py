#!/usr/bin/env python3
"""File GitHub issues for reverse-provenance findings.

Input is the JSON report from scripts/provenance/scan_corpus.py (upstream
files that lack GCC/FSF attribution yet match a GCC file strongly).

Usage:
    scripts/provenance/file_downstream.py /tmp/corpus-vs-gcc.json \
        [--dry-run] [--min-severity high|critical] [--limit N] \
        [--repo krystophny/gcc-dev]

Suppresses entries that already appear in open or closed
`provenance:downstream`-labelled issues on the target repo.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SEV_RANK = {"low": 0, "medium": 1, "review": 2, "high": 3, "critical": 4}

# Upstream-tracker map; mirror of scan_downstream.py TRACKERS. Centralising
# here would be cleaner but the duplication keeps the two scripts
# independently shippable.
TRACKERS = {
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
    "boost-charconv": ("https://github.com/boostorg/charconv/issues", "boostorg/charconv issues"),
    "freebsd-libc": ("https://bugs.freebsd.org/bugzilla/", "FreeBSD Bugzilla"),
    "netbsd-libc": ("https://gnats.netbsd.org/", "NetBSD GNATS"),
    "openbsd-libc": ("https://www.openbsd.org/report.html", "OpenBSD bug reporting"),
    "musl": ("https://www.openwall.com/lists/musl/", "musl mailing list"),
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
    "llvm-project": ("https://github.com/llvm/llvm-project/issues", "llvm/llvm-project issues"),
    "newlib-cygwin": ("https://sourceware.org/bugzilla/enter_bug.cgi?product=newlib", "newlib Bugzilla"),
    "gnulib": ("https://lists.gnu.org/mailman/listinfo/bug-gnulib", "bug-gnulib mailing list"),
    "gettext": ("https://savannah.gnu.org/bugs/?group=gettext", "gettext Savannah"),
    "dmd-druntime": ("https://github.com/dlang/dmd/issues", "dlang/dmd issues"),
    "gofrontend": ("https://github.com/golang/gofrontend/issues", "golang/gofrontend issues"),
    "rustc": ("https://github.com/rust-lang/rust/issues", "rust-lang/rust issues"),
    "glibc": ("https://sourceware.org/bugzilla/enter_bug.cgi?product=glibc", "glibc Bugzilla"),
    "ulfjack-ryu": ("https://github.com/ulfjack/ryu/issues", "ulfjack/ryu issues"),
    "fmtlib": ("https://github.com/fmtlib/fmt/issues", "fmtlib/fmt issues"),
    "a68g": ("https://github.com/dvirtz/Algol68G-mirror/issues", "Algol68G issues"),
    "libatomic_ops": ("https://github.com/ivmai/libatomic_ops/issues", "ivmai/libatomic_ops issues"),
    "gnucobol": ("https://github.com/OCamlPro/gnucobol/issues", "OCamlPro/gnucobol issues"),
    "gmp": ("https://gmplib.org/list-archives/gmp-bugs/", "gmp-bugs mailing list"),
    "libunistring": ("https://savannah.gnu.org/bugs/?group=libunistring", "libunistring Savannah"),
}

# Expected-false-positive patterns we suppress up front. These are pairs
# where content overlap is explained by a common non-GCC upstream or an
# acknowledged GCC-to-external port, documented elsewhere in the repo.
FALSE_POSITIVE_RULES: tuple[tuple[re.Pattern, re.Pattern], ...] = (
    # ulfjack/ryu shared source between libstdc++-v3 and many upstreams
    # (ulfjack-ryu itself, libcxx, llvm-libc, picolibc, postgresql common,
    # microsoft-stl, boost-charconv, dragonbox). Scanner match is cross-
    # upstream triangulation through Ulf Adams' Apache-2.0/Boost upstream.
    (re.compile(r"(ulfjack-ryu|picolibc/libc/stdio|llvm-project/(libcxx|libc)|"
                r"postgresql/src/common|microsoft-stl|boost-charconv|dragonbox)/"
                r".*(ryu|charconv|digit_table|dtoa_ryu|ftoa_ryu|divpow2)"),
     re.compile(r"libstdc\+\+-v3/src/c\+\+17/ryu/")),
    # gccrs / gccgo ports — GCC is the downstream.
    (re.compile(r"gofrontend/go/"), re.compile(r"gcc/(rust|algol68)/")),
    # Visium sibling sync (newlib/picolibc) already reviewed.
    (re.compile(r"(newlib-cygwin|picolibc)/.*/visium/"),
     re.compile(r"libgcc/config/visium/")),
    # rl78 sibling sync already reviewed.
    (re.compile(r"newlib-cygwin/libgloss/rl78/"),
     re.compile(r"libgcc/config/rl78/")),
    # Sun/FreeBSD msun shared libm code. Covers:
    #   openlibm/{src,ld80,ld128}/
    #   newlib-cygwin/newlib/libm/{math,ld128}/
    #   picolibc/libm/{math,ld/ld128}/
    #   bionic/libm/upstream-freebsd/lib/msun/{src,ld128}/
    #   apple-libc math paths
    #   musl/src/math/
    # Every upstream attributes Sun Microsystems; GCC libquadmath carries
    # Moshier's 2001 LGPL reworks. Neither direction is theft.
    (re.compile(r"(newlib-cygwin|picolibc|openlibm|bionic|apple-libc|musl)/"
                r"(?:[^/]+/)*(math|msun|ld128|ld80|libm|src)/"),
     re.compile(r"libquadmath/math/")),
    # IBM decNumber: Mike Cowlishaw / IBM's General Decimal Arithmetic
    # library. Both ICU and GCC libdecnumber import it independently and
    # attribute IBM in their respective headers.
    (re.compile(r"icu/.*/(decNumber|decContext|decimfmt|number_decimalquantity|"
                r"fmtable|decimfmtimpl|plurrule|format|digitlst)"),
     re.compile(r"libdecnumber/")),
    # UC Berkeley BSD utilities shared between BSD libc family, Apple libc,
    # PostgreSQL src/port, illumos (Solaris-BSD), newlib-cygwin, bionic,
    # and libiberty. libiberty imported from BSD originally; all downstream
    # copies share the original BSD origin.
    (re.compile(r"(freebsd-libc|netbsd-libc|openbsd-libc|apple-libc|"
                r"postgresql|bionic|illumos|newlib-cygwin)/"
                r".*(bsearch|strtol|strtoul|strtod|strtoq|strtouq|strtoll|"
                r"strtoull|strtoimax|strtoumax|wcstol|wcstoll|"
                r"strncasecmp|strcasecmp|strcase_charmap|"
                r"strchr|strrchr|memchr|memcmp|memcpy|memmove|memset|"
                r"qsort|getopt|vasprintf|asprintf|snprintf|strlcpy|strlcat|"
                r"index\.c|rindex\.c|strdup|strndup|strerror|strsignal|"
                r"strstr|strspn|strcspn|strpbrk|strtok|strxfrm)"),
     re.compile(r"libiberty/")),
    # gmon / sol2 gmon — newlib's mep-gmon.c is sibling to libgcc/config/sol2
    # (both are variants of the original 4BSD gmon, Gnu reimplementation).
    (re.compile(r"newlib-cygwin/.*(gmon|mcount)"),
     re.compile(r"libgcc/config/sol2/")),
    # glibc tens_in_limb.c: libquadmath imports from glibc (issue #121);
    # glibc is the source, not downstream.
    (re.compile(r"glibc/stdlib/tens_in_limb"),
     re.compile(r"libquadmath/strtod/tens_in_limb")),
    # glibc md5 / locale programs md5-block: libiberty imports from gnulib,
    # glibc imports its own md5 from the same upstream; sibling.
    (re.compile(r"glibc/.*/md5"), re.compile(r"libiberty/md5")),
    # RISC-V ABI feature_bits: coordinated cross-compiler ABI (issue #122).
    (re.compile(r"llvm-project/compiler-rt/lib/builtins/cpu_model/riscv"),
     re.compile(r"libgcc/config/riscv/feature_bits")),
)


def load_suppressed(repo: str) -> set[tuple[str, str]]:
    """Load (upstream_project, upstream_relpath) pairs already tracked."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", repo,
             "--state", "all", "--label", "provenance:downstream",
             "--limit", "500", "--json", "title,body"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        return set()
    title_re = re.compile(
        r"\[[^\]]+\]\s*downstream-provenance:\s*(?P<up>\S+)\s*<-\s*", re.IGNORECASE
    )
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        t = (issue.get("title") or "")
        m = title_re.match(t)
        if not m:
            continue
        upstream = m.group("up")
        project, _, rel = upstream.partition("/")
        if project and rel:
            seen.add((project, rel))
    return seen


def is_false_positive(project: str, relpath: str, gcc_relpath: str) -> bool:
    upstream = f"{project}/{relpath}"
    gcc = f"gcc/{gcc_relpath}"
    for up_pat, gcc_pat in FALSE_POSITIVE_RULES:
        if up_pat.search(upstream) and gcc_pat.search(gcc):
            return True
    return False


def render_body(finding: dict) -> str:
    project = finding["project"]
    rel = finding["relpath"]
    sev = finding["severity"]
    hdr = finding.get("header_class", "?")
    matches = finding.get("matches") or []
    best = matches[0] if matches else {}
    tracker = TRACKERS.get(project, ("", ""))
    lines = [
        "## Finding",
        "",
        f"Upstream `{project}/{rel}` lacks GCC/FSF attribution yet matches",
        f"`gcc/{best.get('relpath','?')}` strongly. This is the reverse-provenance",
        "direction: external project carrying GCC content without the RLE notice.",
        "",
        "## Evidence",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| severity (scanner) | {sev} |",
        f"| score | {finding.get('score', 0.0):.2f} |",
        f"| upstream header class | {hdr} |",
        f"| GCC counterpart | `gcc/{best.get('relpath','?')}` |",
        f"| winnow density | {best.get('winnow_density','?')} |",
        f"| shingle Jaccard | {best.get('shingle_jaccard','?')} |",
        f"| line Jaccard | {best.get('line_jaccard','?')} |",
        f"| longest run | {best.get('longest_run','?')} |",
        f"| TLSH distance | {best.get('tlsh_distance','?')} |",
        "",
    ]
    excerpt = finding.get("header_excerpt", "")
    if excerpt:
        lines += ["## Upstream header excerpt", "", "```", excerpt, "```", ""]
    if tracker[0]:
        lines += [
            "## Upstream tracker",
            "",
            f"- {tracker[1]}: {tracker[0]}",
            "",
            "File the upstream fix on that tracker; this issue is the gcc-dev",
            "tracking handle.",
            "",
        ]
    lines += textwrap.dedent(f"""
    ## Research workflow

    Before filing upstream, deepen the corpus clone for directionality
    (`git -C corpusbin/src/{project} fetch --depth=50000 origin`) and confirm
    from git dates that GCC is genuinely the older copy. Document the
    chain in this issue body; record the registry decision in
    `.provenance/source-review.toml`.
    """).splitlines()
    return "\n".join(lines)


def title_for(finding: dict) -> str:
    sev = finding.get("severity", "low")
    best = (finding.get("matches") or [{}])[0]
    gcc_rel = best.get("relpath", "?")
    prefix = {"critical": "CRITICAL", "high": "HIGH"}.get(sev, sev.upper())
    return f"[{prefix}] downstream-provenance: {finding['project']}/{finding['relpath']} <- gcc/{gcc_rel}"


def gh_create(finding: dict, repo: str, labels: list[str], dry_run: bool):
    title = title_for(finding)
    body = render_body(finding)
    sev = finding.get("severity", "low")
    sev_label = f"severity:{sev}" if sev in ("critical", "high", "medium", "low") else None
    applied = list(labels)
    if sev_label and sev_label not in applied:
        applied.append(sev_label)
    if dry_run:
        print(f"--- {title}  labels={applied}")
        print(body)
        print()
        return None
    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
    for lab in applied:
        cmd += ["--label", lab]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print(f"FAIL {title}: {exc.stderr}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--repo", default="krystophny/gcc-dev")
    parser.add_argument("--label", action="append", default=[],
                        help="Labels (repeatable). Default: provenance,provenance:downstream")
    parser.add_argument("--min-severity", default="high",
                        choices=("medium", "high", "critical"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.label:
        args.label = ["provenance", "provenance:downstream"]

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"report not found: {report_path}", file=sys.stderr)
        return 1
    data = json.loads(report_path.read_text(encoding="utf-8"))
    findings = data.get("findings", []) or []

    suppressed = load_suppressed(args.repo)
    min_rank = SEV_RANK[args.min_severity]

    filtered = []
    seen: set[tuple[str, str]] = set()
    for f in findings:
        project = f.get("project")
        rel = f.get("relpath")
        if not project or not rel:
            continue
        key = (project, rel)
        if key in seen or key in suppressed:
            continue
        if SEV_RANK.get(f.get("severity", "low"), 0) < min_rank:
            continue
        matches = f.get("matches") or []
        if not matches:
            continue
        gcc_rel = matches[0].get("relpath", "")
        if is_false_positive(project, rel, gcc_rel):
            continue
        seen.add(key)
        filtered.append(f)

    filtered.sort(key=lambda f: (-SEV_RANK.get(f.get("severity", "low"), 0),
                                  -float(f.get("score", 0.0)),
                                  f["project"], f["relpath"]))
    if args.limit is not None:
        filtered = filtered[: args.limit]

    print(f"findings_total={len(findings)} unreviewed={len(filtered)}"
          f" suppressed={len(suppressed)} min={args.min_severity}")

    created = 0
    for f in filtered:
        url = gh_create(f, args.repo, args.label, args.dry_run)
        if url:
            created += 1
            print(f"  {f['severity']:8s} {url}  {f['project']}/{f['relpath']}")
    if not args.dry_run:
        print(f"issues_created={created}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
