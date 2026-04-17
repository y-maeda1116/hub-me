#!/usr/bin/env python3
"""Update README.md by replacing tagged sections with dynamic content."""
import argparse
import json
import re
import subprocess
import sys

OWNER = "y-maeda1116"


def replace_section(content: str, tag: str, new_content: str) -> str:
    """Replace content between <!-- TAG --> and <!-- /TAG --> markers.

    Tags and surrounding structure are preserved; only inner content changes.
    Returns original content if tag not found.
    """
    pattern = rf"(<!--\s*{tag}\s*-->)(.*?)(<!--\s*/{tag}\s*-->)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content
    return content[:match.start()] + f"<!-- {tag} -->\n{new_content}\n<!-- /{tag} -->" + content[match.end():]


def format_repo_status_table(status_json: str, owner: str) -> str:
    """Convert repo status JSON into a markdown table."""
    try:
        repos = json.loads(status_json)
    except (json.JSONDecodeError, TypeError):
        return "| Repository | Latest Release | Build Status |\n|---|---|---|\n| Error loading data | - | - |"

    status_icons = {
        "success": "![passing](https://img.shields.io/badge/build-passing-brightgreen)",
        "failure": "![failing](https://img.shields.io/badge/build-failing-red)",
    }

    lines = ["| Repository | Latest Release | Build Status |", "|---|---|---|"]
    for repo in repos:
        name = repo.get("name", "unknown")
        release = repo.get("latest_release", "N/A")
        build = repo.get("build_status", "N/A")
        icon = status_icons.get(
            build,
            f"![{build}](https://img.shields.io/badge/build/{build}-lightgrey)",
        )
        lines.append(
            f"| [{name}](https://github.com/{owner}/{name}) | `{release}` | {icon} |"
        )
    return "\n".join(lines)


def format_recent_commits(commits: list) -> str:
    """Format a list of commit dicts into markdown list items."""
    if not commits:
        return "No recent activity"
    lines = []
    for c in commits:
        repo = c.get("repo", "").split("/")[-1]
        message = c.get("message", "").split("\n")[0]
        date = c.get("date", "")[:10]
        lines.append(f"- `{repo}` — {message} (_{date}_)")
    return "\n".join(lines)


def fetch_recent_commits(owner: str, limit: int = 3) -> list:
    """Fetch recent push events via gh CLI and return commit dicts."""
    result = subprocess.run(
        [
            "gh",
            "api",
            f"users/{owner}/events/public?per_page=100",
            "--jq",
            '[.[] | select(.type == "PushEvent") | {repo: .repo.name, message: .payload.commits[0].message, date: .created_at}][:5]',
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        events = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    seen = set()
    unique = []
    for e in events:
        key = (e.get("repo", ""), e.get("message", ""))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique[:limit]


def main():
    parser = argparse.ArgumentParser(
        description="Update README.md dynamic sections"
    )
    parser.add_argument(
        "--readme", default="README.md", help="Path to README.md"
    )
    parser.add_argument(
        "--repo-status-file",
        help="Path to JSON file from fetch_repo_status.py",
    )
    parser.add_argument(
        "--focus-file",
        help="Path to text file from analyze_commits.py",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print result without writing file",
    )
    args = parser.parse_args()

    try:
        with open(args.readme, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {args.readme} not found", file=sys.stderr)
        sys.exit(1)

    new_content = content

    if args.repo_status_file:
        try:
            with open(args.repo_status_file, "r") as f:
                status_json = f.read()
            table = format_repo_status_table(status_json, OWNER)
            new_content = replace_section(
                new_content, "REPO_STATUS_TABLE", table
            )
        except FileNotFoundError:
            print(
                f"Warning: {args.repo_status_file} not found, skipping repo status",
                file=sys.stderr,
            )

    try:
        commits = fetch_recent_commits(OWNER)
        commits_text = format_recent_commits(commits)
        new_content = replace_section(
            new_content, "RECENT_COMMITS", commits_text
        )
    except Exception as e:
        print(
            f"Warning: failed to fetch recent commits: {e}", file=sys.stderr
        )

    if args.focus_file:
        try:
            with open(args.focus_file, "r") as f:
                focus_text = f.read().strip()
            if focus_text:
                new_content = replace_section(
                    new_content, "CURRENT_FOCUS", focus_text
                )
        except FileNotFoundError:
            print(
                f"Warning: {args.focus_file} not found, skipping focus",
                file=sys.stderr,
            )

    if args.dry_run:
        print(new_content)
    else:
        with open(args.readme, "w") as f:
            f.write(new_content)
        print(f"Updated {args.readme}")


if __name__ == "__main__":
    main()
