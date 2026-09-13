#!/usr/bin/env python3
"""Generate an SVG card showing commits per day of week."""
import argparse
import html
import json
import math
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

OWNER = "y-maeda1116"

RETRY_MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 60

MAX_PAGES = 10  # Search API serves at most 1000 results (PER_PAGE per page)
PER_PAGE = 100
PAGE_DELAY_SECONDS = 2.0  # back-to-back search requests trip secondary limits


def run_gh_api(args: list[str]):
    """Run `gh api`, retrying transient failures with linear backoff.

    GitHub's secondary rate limit answers HTTP 403 with "wait a few
    minutes" even when the primary quota is fine, so a burst of API
    calls from another step can fail these requests. Retrying keeps a
    transient 403 from failing the whole daily run.
    """
    result = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        result = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
        if result.returncode == 0 or attempt == RETRY_MAX_ATTEMPTS:
            return result
        delay = RETRY_DELAY_SECONDS * attempt
        print(
            f"warning: gh api {args[0][:80]} failed (rc={result.returncode}); "
            f"retrying in {delay}s: {(result.stderr or '').strip()[:200]}",
            file=sys.stderr,
        )
        time.sleep(delay)
    return result

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

BG_COLOR = "#ffffff"
BORDER_COLOR = "#e4e2e2"
BAR_COLOR = "#586e75"
TEXT_COLOR = "#586e75"


def parse_commit_date(date_str: str) -> datetime | None:
    """Parse an ISO-8601 commit date, returning None when malformed."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (AttributeError, ValueError, TypeError):
        return None


def _fetch_commit_page(owner: str, qualifier: str, page: int) -> list[str] | None:
    """Fetch one search/commits page; returns None on API failure."""
    result = run_gh_api(
        [f"search/commits?q=author:{owner}{qualifier}&sort=committer-date&per_page={PER_PAGE}&page={page}",
         "--jq", '[.items[] | .commit.author.date]'],
    )
    if result.returncode != 0 or not result.stdout.strip():
        print(f"error: gh api search/commits failed (rc={result.returncode}): {(result.stderr or '').strip()}",
              file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"error: gh api search/commits returned invalid JSON: {result.stdout[:200]}",
              file=sys.stderr)
        return None


def _fetch_window(owner: str, start_date=None, end_date=None) -> list[str] | None:
    """Fetch commit dates for one date range (whole history when unbounded).

    Paginates until a short page. Stops at MAX_PAGES — the Search API's
    1000-result cap — and warns when it does, so a full-length result
    means the window is incomplete; callers detect the cap by result
    length.
    """
    qualifier = ""
    if start_date is not None and end_date is not None:
        # author-date matches the extracted .commit.author.date field, so
        # the exact [start, end) filter below never crosses date semantics
        qualifier = f"+author-date:{start_date}..{end_date}"
    dates: list[str] = []
    for page in range(1, MAX_PAGES + 1):
        page_dates = _fetch_commit_page(owner, qualifier, page)
        if page_dates is None:
            return None
        if not page_dates:
            break
        dates.extend(page_dates)
        if len(page_dates) < PER_PAGE:
            break
        if page < MAX_PAGES:
            time.sleep(PAGE_DELAY_SECONDS)
    if len(dates) >= MAX_PAGES * PER_PAGE:
        print(f"warning: results truncated at the {MAX_PAGES * PER_PAGE}-result "
              "search cap", file=sys.stderr)
    return dates


def _window_bounds(since: datetime, now: datetime) -> list[datetime]:
    """Split [since, now] into boundaries of ~30-day half-open windows."""
    span = now - since
    count = max(1, math.ceil(span.total_seconds() / (30 * 86400)))
    return [since + (span / count) * i for i in range(count + 1)]


def fetch_commit_dates(owner: str, since: datetime | None = None) -> list[str] | None:
    """Fetch commit dates via the Search API.

    With since, the span is queried as ~30-day date-range windows: one
    query caps at 1000 results and this account exceeds that per year,
    so windows keep every query complete. Day-granularity ranges are
    tightened with an exact [start, end) filter so boundary commits are
    counted exactly once. A window that still hits the cap returns None
    — incomplete counts would mislabel the card — as does any API
    failure. Without since, returns the newest-first stream up to the
    cap (legacy behavior).
    """
    if since is None:
        return _fetch_window(owner)

    now = datetime.now(timezone.utc)
    bounds = _window_bounds(since, now)
    dates: list[str] = []
    for start, end in zip(bounds, bounds[1:]):
        window_dates = _fetch_window(owner, start_date=start.date(), end_date=end.date())
        if window_dates is None:
            return None
        if len(window_dates) >= MAX_PAGES * PER_PAGE:
            print(f"error: commits in {start.date()}..{end.date()} hit the "
                  f"{MAX_PAGES * PER_PAGE}-result search cap; counts would be incomplete",
                  file=sys.stderr)
            return None
        for date_str in window_dates:
            dt = parse_commit_date(date_str)
            if dt is not None and dt.tzinfo is not None and start <= dt < end:
                dates.append(date_str)
    return dates


def count_by_weekday(dates: list[str], utc_offset: int = 0) -> list[int]:
    """Count commits per weekday (Mon=0 .. Sun=6), applying UTC offset."""
    counter: Counter[int] = Counter()
    for date_str in dates:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            dt = dt + timedelta(hours=utc_offset)
            counter[dt.weekday()] += 1
        except (ValueError, TypeError):
            continue
    return [counter.get(i, 0) for i in range(7)]


def generate_svg(counts: list[int]) -> str:
    """Generate a horizontal bar chart SVG for weekday commits."""
    width = 340
    bar_area_top = 50
    bar_area_height = 140
    label_width = 35
    value_width = 40
    bar_max_width = width - label_width - value_width - 30
    bar_height = 14
    bar_gap = (bar_area_height - 7 * bar_height) / 6

    max_count = max(counts) if counts and max(counts) > 0 else 1

    bars = ""
    for i, count in enumerate(counts):
        y = bar_area_top + i * (bar_height + bar_gap)
        bw = int(count / max_count * bar_max_width) if max_count > 0 else 0
        bars += f'<text x="{label_width}" y="{y + bar_height - 2}" text-anchor="end" fill="{TEXT_COLOR}" font-size="12">{DAY_NAMES[i]}</text>'
        if bw > 0:
            bars += f'<rect x="{label_width + 10}" y="{y}" width="{bw}" height="{bar_height}" rx="3" fill="{BAR_COLOR}"/>'
        bars += f'<text x="{label_width + 10 + bw + 8}" y="{y + bar_height - 2}" fill="{TEXT_COLOR}" font-size="11">{count}</text>'

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="200" viewBox="0 0 {width} 200">'
        f'<style>* {{ font-family: "Segoe UI", Ubuntu, "Helvetica Neue", Sans-Serif }}</style>'
        f'<rect x="1" y="1" rx="5" ry="5" height="99%" width="99.4%" stroke="{BORDER_COLOR}" stroke-width="1" fill="{BG_COLOR}"/>'
        f'<text x="30" y="35" style="font-size: 18px; fill: {TEXT_COLOR};">Commits per Day</text>'
        f'{bars}'
        f'</svg>'
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekday commits SVG card")
    parser.add_argument("--output", required=True, help="Output SVG file path")
    parser.add_argument("--utc-offset", type=int, default=9, help="UTC offset (default: 9)")
    parser.add_argument("--owner", default=OWNER, help="GitHub username")
    parser.add_argument("--days", type=int, default=365,
                        help="Count only commits from the last N days (default: 365)")
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be >= 1")

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    dates = fetch_commit_dates(args.owner, since=since)
    if dates is None:
        print("error: could not fetch commit dates; keeping previous card",
              file=sys.stderr)
        sys.exit(1)
    counts = count_by_weekday(dates, args.utc_offset)
    svg = generate_svg(counts)

    with open(args.output, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
