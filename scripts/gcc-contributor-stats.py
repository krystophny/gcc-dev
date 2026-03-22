#!/usr/bin/env python3
"""Generate GCC trunk contribution statistics with Signed-off-by awareness."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import email.utils
import pathlib
import subprocess
import sys
from dataclasses import dataclass


RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


@dataclass(frozen=True)
class Identity:
    key: str
    name: str
    email: str


@dataclass
class CommitRecord:
    commit_hash: str
    author: Identity
    committer: Identity
    commit_date: str
    signed_off_by: list[Identity]
    lines_added: int = 0
    lines_deleted: int = 0


def run_git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        errors="replace",
    )


def parse_identity(raw_name: str, raw_email: str | None = None) -> Identity:
    if raw_email is None:
        parsed_name, parsed_email = email.utils.parseaddr(raw_name)
    else:
        parsed_name = raw_name.strip()
        parsed_email = raw_email.strip()

    name = parsed_name.strip() or parsed_email.strip() or "(unknown)"
    email_addr = parsed_email.strip().lower()
    key = name.casefold() if parsed_name.strip() else email_addr
    return Identity(key=key, name=name, email=email_addr)


def first_meta_repo_date(meta_repo: pathlib.Path) -> str:
    return run_git(meta_repo, "log", "--reverse", "--format=%cs").splitlines()[0]


def extract_signed_off_by(message: str) -> list[Identity]:
    seen: set[str] = set()
    identities: list[Identity] = []
    for line in message.splitlines():
        if not line.lower().startswith("signed-off-by:"):
            continue
        value = line.split(":", 1)[1].strip()
        ident = parse_identity(value)
        if ident.key in seen:
            continue
        seen.add(ident.key)
        identities.append(ident)
    return identities


def collect_commits(
    repo: pathlib.Path,
    ref: str,
    start: str,
    end: str,
) -> list[CommitRecord]:
    fmt = "%H" + FIELD_SEP + "%aN" + FIELD_SEP + "%aE" + FIELD_SEP
    fmt += "%cN" + FIELD_SEP + "%cE" + FIELD_SEP + "%cI" + FIELD_SEP + "%B" + RECORD_SEP
    raw = run_git(repo, "log", ref, f"--since={start}", f"--until={end}", f"--format={fmt}")
    commits_by_hash: dict[str, CommitRecord] = {}
    for chunk in raw.split(RECORD_SEP):
        if not chunk.strip():
            continue
        parts = chunk.split(FIELD_SEP, 6)
        if len(parts) != 7:
            raise RuntimeError(f"Unexpected git log record shape: {parts!r}")
        commit_hash, author_name, author_email, committer_name, committer_email, commit_date, body = parts
        commit_hash = commit_hash.strip()
        author_name = author_name.strip()
        author_email = author_email.strip()
        committer_name = committer_name.strip()
        committer_email = committer_email.strip()
        commit_date = commit_date.strip()
        author = parse_identity(author_name, author_email)
        committer = parse_identity(committer_name, committer_email)
        commits_by_hash[commit_hash] = CommitRecord(
            commit_hash=commit_hash,
            author=author,
            committer=committer,
            commit_date=commit_date,
            signed_off_by=extract_signed_off_by(body),
        )
    raw_numstat = run_git(
        repo,
        "log",
        ref,
        f"--since={start}",
        f"--until={end}",
        "--numstat",
        "--format=%H",
    )
    current_hash: str | None = None
    for line in raw_numstat.splitlines():
        if not line:
            continue
        if len(line) == 40 and all(ch in "0123456789abcdef" for ch in line):
            current_hash = line
            continue
        if current_hash is None:
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added_raw, deleted_raw, _path = parts
        if added_raw == "-" or deleted_raw == "-":
            continue
        commit = commits_by_hash.get(current_hash)
        if commit is None:
            continue
        commit.lines_added += int(added_raw)
        commit.lines_deleted += int(deleted_raw)
    return list(commits_by_hash.values())


def count_by_identity(
    identities: list[Identity],
) -> tuple[collections.Counter[str], dict[str, str]]:
    counter: collections.Counter[str] = collections.Counter()
    display: dict[str, str] = {}
    for identity in identities:
        counter[identity.key] += 1
        display.setdefault(identity.key, identity.name)
    return counter, display


def make_chart(
    counter: collections.Counter[str],
    display: dict[str, str],
    *,
    top: int,
    width: int,
) -> str:
    items = sorted(counter.items(), key=lambda item: (-item[1], display[item[0]].casefold()))
    if not items:
        return "(no data)"

    top_items = items[:top]
    max_name = max(len(display[key]) for key, _ in top_items)
    max_value = max(value for _, value in top_items)
    lines: list[str] = []
    for key, value in top_items:
        bar_len = max(1, round(value * width / max_value))
        bar = "#" * bar_len
        lines.append(f"{display[key]:<{max_name}}  {value:>4}  {bar}")
    return "\n".join(lines)


def build_patch_histogram(counter: collections.Counter[str]) -> collections.Counter[str]:
    buckets = collections.Counter()
    for value in counter.values():
        if value == 1:
            label = "1"
        elif value == 2:
            label = "2"
        elif value <= 4:
            label = "3-4"
        elif value <= 9:
            label = "5-9"
        elif value <= 19:
            label = "10-19"
        elif value <= 49:
            label = "20-49"
        elif value <= 99:
            label = "50-99"
        else:
            label = "100+"
        buckets[label] += 1
    return buckets


def make_histogram_chart(counter: collections.Counter[str], *, width: int) -> str:
    order = ["1", "2", "3-4", "5-9", "10-19", "20-49", "50-99", "100+"]
    items = [(label, counter[label]) for label in order if counter[label]]
    if not items:
        return "(no data)"
    max_value = max(value for _, value in items)
    max_name = max(len(label) for label, _ in items)
    lines = []
    for label, value in items:
        bar_len = max(1, round(value * width / max_value))
        lines.append(f"{label:<{max_name}}  {value:>4}  {'#' * bar_len}")
    return "\n".join(lines)


def count_loc_by_identity(
    identities: list[Identity],
    commits: list[CommitRecord],
) -> tuple[collections.Counter[str], collections.Counter[str], collections.Counter[str], dict[str, str]]:
    added = collections.Counter()
    deleted = collections.Counter()
    changed = collections.Counter()
    display: dict[str, str] = {}
    for identity, commit in zip(identities, commits, strict=True):
        added[identity.key] += commit.lines_added
        deleted[identity.key] += commit.lines_deleted
        changed[identity.key] += commit.lines_added + commit.lines_deleted
        display.setdefault(identity.key, identity.name)
    return added, deleted, changed, display


def quantile_by_rank(counter: collections.Counter[str], target_key: str) -> tuple[int, int, int, float] | None:
    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    total = len(ordered)
    try:
        rank = next(index for index, (key, _value) in enumerate(ordered, start=1) if key == target_key)
    except StopIteration:
        return None
    quartile = min(4, ((rank - 1) * 4) // total + 1)
    percentile_from_bottom = 100.0 * (total - rank + 1) / total
    return rank, total, quartile, percentile_from_bottom


def render_markdown(
    *,
    title: str,
    repo: pathlib.Path,
    ref: str,
    start: str,
    end: str,
    commits: list[CommitRecord],
    top: int,
    width: int,
) -> str:
    total = len(commits)
    with_sob = sum(1 for commit in commits if commit.signed_off_by)
    author_ne_committer = sum(1 for commit in commits if commit.author.key != commit.committer.key)

    authors, author_display = count_by_identity([commit.author for commit in commits])
    committers, committer_display = count_by_identity([commit.committer for commit in commits])
    primary_contributors, primary_display = count_by_identity(
        [commit.signed_off_by[0] if commit.signed_off_by else commit.author for commit in commits]
    )
    signoff_appearances, signoff_display = count_by_identity(
        [identity for commit in commits for identity in commit.signed_off_by]
    )
    primary_identities = [commit.signed_off_by[0] if commit.signed_off_by else commit.author for commit in commits]
    primary_loc_added, primary_loc_deleted, primary_loc_changed, primary_loc_display = count_loc_by_identity(
        primary_identities,
        commits,
    )
    patch_histogram = build_patch_histogram(primary_contributors)
    total_added = sum(commit.lines_added for commit in commits)
    total_deleted = sum(commit.lines_deleted for commit in commits)
    total_changed = total_added + total_deleted
    christopher = parse_identity("Christopher Albert", "")
    christopher_quantile = quantile_by_rank(
        primary_contributors,
        christopher.key,
    )
    contributor_count = len(primary_contributors)
    christopher_patches = primary_contributors[christopher.key]
    christopher_loc = primary_loc_changed[christopher.key]

    generated = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    distribution_lines = [
        f"- **Contributors with at least one attributed patch:** `{contributor_count}`",
        f"- **Christopher Albert primary-contributor patches:** `{christopher_patches}`",
    ]
    if christopher_quantile is not None:
        christopher_rank, _total, christopher_quartile, christopher_percentile = christopher_quantile
        distribution_lines.extend(
            [
                f"- **Christopher Albert primary-contributor rank:** `{christopher_rank}` / `{contributor_count}`",
                f"- **Christopher Albert quantile by rank:** `Q{christopher_quartile}`",
                f"- **Christopher Albert percentile from bottom:** `{christopher_percentile:.1f}`",
            ]
        )

    lines = [
        f"# {title}",
        "",
        f"- **Generated:** {generated}",
        f"- **Repository:** `{repo}`",
        f"- **Reference:** `{ref}`",
        f"- **Date range:** `{start}` to `{end}`",
        f"- **Total trunk commits:** `{total}`",
        f"- **Commits with Signed-off-by:** `{with_sob}`",
        f"- **Commits where author != committer:** `{author_ne_committer}`",
        "",
        "## Attribution Rules",
        "",
        "- `Primary contributor` = first `Signed-off-by:` trailer when present, otherwise the Git author.",
        "- Commits are attributed once for contributor metrics; when `Signed-off-by:` is present, the committer is not counted as the contributor.",
        "- `Committer` = the person who landed the commit on trunk.",
        "- `Signed-off-by appearances` counts unique signers per commit.",
        "",
        "## Distribution Summary",
        "",
        *distribution_lines,
        "",
        "## Histogram: Patches per Primary Contributor",
        "",
        "```text",
        make_histogram_chart(patch_histogram, width=width),
        "```",
        "",
        "## Top Primary Contributors",
        "",
        "```text",
        make_chart(primary_contributors, primary_display, top=top, width=width),
        "```",
        "",
        "## Lines of Code (Primary Contributor Attribution)",
        "",
        f"- **Total lines added:** `{total_added}`",
        f"- **Total lines deleted:** `{total_deleted}`",
        f"- **Total lines changed:** `{total_changed}`",
        f"- **Christopher Albert lines changed:** `{christopher_loc}`",
        "",
        "### Top Primary Contributors by Lines Changed",
        "",
        "```text",
        make_chart(primary_loc_changed, primary_loc_display, top=top, width=width),
        "```",
        "",
        "## Top Authors",
        "",
        "```text",
        make_chart(authors, author_display, top=top, width=width),
        "```",
        "",
        "## Top Committers",
        "",
        "```text",
        make_chart(committers, committer_display, top=top, width=width),
        "```",
        "",
        "## Top Signed-off-by Appearances",
        "",
        "```text",
        make_chart(signoff_appearances, signoff_display, top=top, width=width),
        "```",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="gcc", help="Path to the GCC git checkout.")
    parser.add_argument(
        "--meta-repo",
        default=".",
        help="Path to the meta-repo used to derive the default start date.",
    )
    parser.add_argument("--ref", default="upstream/master", help="Git ref to analyse.")
    parser.add_argument("--title", default="GCC Trunk Contributor Statistics", help="Markdown report title.")
    parser.add_argument("--start", help="Inclusive start date (YYYY-MM-DD). Defaults to meta-repo creation date.")
    parser.add_argument(
        "--end",
        default=dt.date.today().isoformat(),
        help="Inclusive end date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument("--top", type=int, default=40, help="Number of rows per chart.")
    parser.add_argument("--width", type=int, default=40, help="Bar width in characters.")
    parser.add_argument("--output", help="Write markdown report to this file instead of stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = pathlib.Path(args.repo).resolve()
    meta_repo = pathlib.Path(args.meta_repo).resolve()
    start = args.start or first_meta_repo_date(meta_repo)
    commits = collect_commits(repo, args.ref, start, args.end)
    report = render_markdown(
        title=args.title,
        repo=repo,
        ref=args.ref,
        start=start,
        end=args.end,
        commits=commits,
        top=args.top,
        width=args.width,
    )
    if args.output:
        pathlib.Path(args.output).write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
