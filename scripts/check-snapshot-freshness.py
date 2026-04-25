#!/usr/bin/env python3
"""Warn when generated docs go stale.

Scans tracked docs/*.md for a `Generated: <ISO date>` or `Snapshot date:
<ISO date>` line in the first 30 lines and warns if it is older than
--warn-days (default 30). Local-only; never queries upstream.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATE_RE = re.compile(
    r"\b(?:Generated|Snapshot date|Snapshot|Last updated)[:\s\*]+(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


def tracked_docs() -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "docs/*.md"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return [ROOT / p for p in out]


def first_date(text: str) -> dt.date | None:
    head = "\n".join(text.splitlines()[:30])
    match = DATE_RE.search(head)
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-days", type=int, default=30)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any stale snapshot")
    args = parser.parse_args()

    today = dt.date.today()
    stale = 0
    no_date = 0
    for path in tracked_docs():
        text = path.read_text(encoding="utf-8")
        date = first_date(text)
        rel = path.relative_to(ROOT)
        if date is None:
            no_date += 1
            continue
        age = (today - date).days
        if age > args.warn_days:
            print(f"warn: {rel}: snapshot date {date} is {age}d old (>{args.warn_days}d)")
            stale += 1
    print(f"checked {len(tracked_docs())} doc(s); {stale} stale, {no_date} without snapshot date")
    return 1 if stale and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
