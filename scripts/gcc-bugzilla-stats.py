#!/usr/bin/env python3
"""Generate lightweight GCC Bugzilla statistics and daily-resolution plots."""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Callable

import requests


UTC = dt.timezone.utc
BUGZILLA_BASE = "https://gcc.gnu.org/bugzilla"
REST_BUG = f"{BUGZILLA_BASE}/rest.cgi/bug"
CLOSED_STATUSES = {"RESOLVED", "VERIFIED", "CLOSED"}
OPEN_STATUSES = ["UNCONFIRMED", "NEW", "ASSIGNED", "SUSPENDED", "WAITING", "REOPENED"]


def today_utc() -> dt.date:
    return dt.datetime.now(UTC).date()


def default_start() -> dt.date:
    return today_utc() - dt.timedelta(days=365)


def parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def parse_datetime(value: str) -> dt.datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return dt.datetime.fromisoformat(value).astimezone(UTC)


def daterange(start: dt.date, end: dt.date) -> list[dt.date]:
    days = (end - start).days
    return [start + dt.timedelta(days=offset) for offset in range(days + 1)]


def is_regression(summary: str) -> bool:
    return "regression" in summary.casefold()


def is_bug(record: dict) -> bool:
    return record.get("bug_severity", "").casefold() != "enhancement"


def category_defs() -> "OrderedDict[str, tuple[str, Callable[[dict], bool]]]":
    return OrderedDict(
        [
            ("all-bugs", ("All GCC bugs", lambda bug: is_bug(bug))),
            (
                "regression-bugs",
                ("All GCC regressions", lambda bug: is_bug(bug) and is_regression(bug.get("summary", ""))),
            ),
            (
                "fortran-bugs",
                ("All Fortran bugs", lambda bug: bug.get("component") == "fortran" and is_bug(bug)),
            ),
            (
                "fortran-regressions",
                (
                    "Fortran regressions",
                    lambda bug: bug.get("component") == "fortran" and is_bug(bug) and is_regression(bug.get("summary", "")),
                ),
            ),
        ]
    )


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "gcc-dev-bugzilla-stats/1.0"})
    return session


def rest_search(session: requests.Session, **params: object) -> list[dict]:
    flat_params: list[tuple[str, str]] = []
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            for item in value:
                flat_params.append((key, str(item)))
        elif value is not None:
            flat_params.append((key, str(value)))
    response = session.get(REST_BUG, params=flat_params, timeout=180)
    response.raise_for_status()
    payload = response.json()
    return payload["bugs"]


def bug_history(session: requests.Session, bug_id: int, start: dt.date, cache_dir: Path) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{bug_id}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    response = session.get(
        f"{REST_BUG}/{bug_id}/history",
        params={"new_since": start.isoformat()},
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()
    cache_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def first_resolution_date(history_payload: dict, start: dt.date) -> dt.date | None:
    bugs = history_payload.get("bugs", [])
    if not bugs:
        return None
    for event in bugs[0].get("history", []):
        when = parse_datetime(event["when"]).date()
        if when < start:
            continue
        changes = event.get("changes", [])
        resolution_added = any(
            change.get("field_name") == "resolution" and change.get("added", "").strip()
            for change in changes
        )
        status_closed = any(
            change.get("field_name") == "bug_status" and change.get("added") in CLOSED_STATUSES
            for change in changes
        )
        if resolution_added or status_closed:
            return when
    return None


def counter_to_series(counter: Counter[dt.date], days: list[dt.date]) -> list[int]:
    return [counter.get(day, 0) for day in days]


def compute_open_series(
    current_open: int,
    created: Counter[dt.date],
    resolved: Counter[dt.date],
    days: list[dt.date],
) -> list[int]:
    total_created = sum(created.values())
    total_resolved = sum(resolved.values())
    baseline = current_open - total_created + total_resolved
    series: list[int] = []
    running = baseline
    for day in days:
        running += created.get(day, 0)
        running -= resolved.get(day, 0)
        series.append(running)
    return series


def render_plots(
    out_dir: Path,
    days: list[dt.date],
    series_data: dict[str, dict[str, object]],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    plot_paths: list[Path] = []
    x = [dt.datetime.combine(day, dt.time.min, tzinfo=UTC) for day in days]

    for slug, data in series_data.items():
        fig, (ax_top, ax_bottom) = plt.subplots(
            2,
            1,
            figsize=(14, 8),
            sharex=True,
            gridspec_kw={"height_ratios": [2, 1]},
        )
        ax_top.plot(x, data["open_series"], color="#005a9c", linewidth=2)
        ax_top.set_title(f"{data['title']} — open backlog")
        ax_top.set_ylabel("Open bugs")
        ax_top.grid(True, alpha=0.3)

        ax_bottom.bar(x, data["created_series"], width=1.0, color="#4caf50", alpha=0.7, label="Opened")
        ax_bottom.bar(x, [-value for value in data["resolved_series"]], width=1.0, color="#d73a49", alpha=0.7, label="Resolved")
        ax_bottom.set_title("Daily opened / resolved")
        ax_bottom.set_ylabel("Daily count")
        ax_bottom.grid(True, alpha=0.3)
        ax_bottom.legend()

        ax_bottom.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        fig.tight_layout()

        path = out_dir / f"{slug}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        plot_paths.append(path)

    return plot_paths


def upload_litterbox(path: Path) -> str:
    response = requests.post(
        "https://litterbox.catbox.moe/resources/internals/api.php",
        data={"reqtype": "fileupload", "time": "72h"},
        files={"fileToUpload": (path.name, path.read_bytes())},
        timeout=180,
    )
    response.raise_for_status()
    return response.text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=parse_date, default=default_start(), help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=parse_date, default=today_utc(), help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/tmp/gcc-bugzilla-stats"),
        help="Directory for plots and JSON output",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".cache" / "gcc-dev-bugzilla-stats",
        help="Directory for cached bug history responses",
    )
    parser.add_argument("--max-workers", type=int, default=4, help="Concurrent history fetches")
    parser.add_argument("--pause", type=float, default=0.05, help="Pause between history requests per worker")
    args = parser.parse_args()

    start = args.start
    end = args.end
    if end < start:
        raise SystemExit("--end must be on or after --start")

    out_dir = args.out_dir
    cache_dir = args.cache_dir / start.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    session = build_session()
    include_fields = "id,component,summary,bug_severity,creation_time,last_change_time,resolution,status"

    open_bugs = rest_search(
        session,
        product="gcc",
        status=OPEN_STATUSES,
        limit=0,
        include_fields=include_fields,
    )
    created_since = rest_search(
        session,
        product="gcc",
        creation_time=start.isoformat(),
        limit=0,
        include_fields=include_fields,
    )
    closed_changed_since = rest_search(
        session,
        product="gcc",
        last_change_time=start.isoformat(),
        status=["RESOLVED", "VERIFIED", "CLOSED"],
        limit=0,
        include_fields=include_fields,
    )

    categories = category_defs()
    days = daterange(start, end)
    resolved_dates: dict[int, dt.date] = {}
    closed_ids = sorted({int(bug["id"]) for bug in closed_changed_since})

    def fetch_resolution(bug_id: int) -> tuple[int, dt.date | None]:
        local_session = build_session()
        try:
            history = bug_history(local_session, bug_id, start, cache_dir)
            return bug_id, first_resolution_date(history, start)
        finally:
            local_session.close()
            if args.pause:
                time.sleep(args.pause)

    with cf.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for bug_id, resolved_date in executor.map(fetch_resolution, closed_ids):
            if resolved_date is not None and resolved_date <= end:
                resolved_dates[bug_id] = resolved_date

    summary: dict[str, dict[str, object]] = OrderedDict()
    plot_inputs: dict[str, dict[str, object]] = OrderedDict()

    for slug, (title, predicate) in categories.items():
        current_open = sum(1 for bug in open_bugs if predicate(bug))
        created_counter: Counter[dt.date] = Counter()
        resolved_counter: Counter[dt.date] = Counter()

        for bug in created_since:
            if predicate(bug):
                created_day = parse_datetime(bug["creation_time"]).date()
                if start <= created_day <= end:
                    created_counter[created_day] += 1

        for bug in closed_changed_since:
            if not predicate(bug):
                continue
            resolved_day = resolved_dates.get(int(bug["id"]))
            if resolved_day is not None and start <= resolved_day <= end:
                resolved_counter[resolved_day] += 1

        created_series = counter_to_series(created_counter, days)
        resolved_series = counter_to_series(resolved_counter, days)
        open_series = compute_open_series(current_open, created_counter, resolved_counter, days)

        summary[slug] = {
            "title": title,
            "current_open": current_open,
            "opened_last_year": sum(created_series),
            "resolved_last_year": sum(resolved_series),
            "start_open": open_series[0],
            "end_open": open_series[-1],
        }
        plot_inputs[slug] = {
            "title": title,
            "created_series": created_series,
            "resolved_series": resolved_series,
            "open_series": open_series,
        }

    plot_paths = render_plots(out_dir, days, plot_inputs)
    uploads = {path.name: upload_litterbox(path) for path in plot_paths}

    summary_payload = {
        "generated_at": dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "method": {
            "bulk_search_endpoint": "GET /bugzilla/rest.cgi/bug",
            "history_endpoint": "GET /bugzilla/rest.cgi/bug/<id>/history?new_since=YYYY-MM-DD",
            "notes": [
                "Current open counts come from one bulk open-bug search.",
                "Created counts come from one bulk search filtered by creation_time.",
                "Exact daily resolution dates are derived from cached history lookups for bugs closed/changed in-range.",
                "Regression classification follows GCC convention used in this repo: summary contains 'regression'.",
                "Enhancement requests are excluded from the bug-category totals.",
            ],
        },
        "summary": summary,
        "plots": uploads,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    print(json.dumps(summary_payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
