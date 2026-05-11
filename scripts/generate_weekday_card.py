#!/usr/bin/env python3
"""Generate an SVG card showing commits per day of week."""
import argparse
import html
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

OWNER = "y-maeda1116"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

BG_COLOR = "#ffffff"
BORDER_COLOR = "#e4e2e2"
BAR_COLOR = "#586e75"
TEXT_COLOR = "#586e75"


def fetch_commit_dates(owner: str) -> list[str]:
    """Fetch commit dates via Search API with pagination."""
    dates: list[str] = []
    page = 1
    while True:
        result = subprocess.run(
            [
                "gh", "api",
                f"search/commits?q=author:{owner}&sort=committer-date&per_page=100&page={page}",
                "--jq",
                '[.items[] | .commit.author.date]',
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            break
        try:
            page_dates = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not page_dates:
            break
        dates.extend(page_dates)
        if len(page_dates) < 100:
            break
        page += 1
    return dates


def count_by_weekday(dates: list[str], utc_offset: int = 0) -> list[int]:
    """Count commits per weekday (Mon=0 .. Sun=6), applying UTC offset."""
    counter: Counter[int] = Counter()
    for date_str in dates:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            from datetime import timedelta
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
    args = parser.parse_args()

    dates = fetch_commit_dates(args.owner)
    counts = count_by_weekday(dates, args.utc_offset)
    svg = generate_svg(counts)

    with open(args.output, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
