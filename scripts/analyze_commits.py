#!/usr/bin/env python3
"""Analyze past week's commits to detect technology trends."""
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from gh_api import OWNER, run_gh_api

EXT_TO_TECH = {
    ".go": "Go",
    ".tf": "Terraform",
    ".hcl": "Terraform",
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".dart": "Dart",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".php": "PHP",
    ".sh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
}

FILENAME_TO_TECH = {
    "dockerfile": "Docker",
    "makefile": "Make",
}


def detect_tech_from_files(files: list[str]) -> list[str]:
    """Detect technologies from file paths."""
    techs = []
    for f in files:
        filename = f.split("/")[-1].lower()
        if filename in FILENAME_TO_TECH:
            techs.append(FILENAME_TO_TECH[filename])
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1]
            if ext in EXT_TO_TECH:
                techs.append(EXT_TO_TECH[ext])
    return techs


def get_active_repos(owner: str, since: str) -> list[str] | None:
    """Get repos owned by `owner` with push events since given date.

    Pushes to organization repositories are excluded. Returns None on
    API failure so the caller can abort instead of writing "No activity
    this week".
    """
    result = run_gh_api(
        [f"users/{owner}/events/public?per_page=100",
         "--jq", f'[.[] | select(.type == "PushEvent" and .created_at >= "{since}") | .repo.name] | unique'],
    )
    if result.returncode != 0 or not result.stdout.strip():
        print(f"error: gh api events/public failed (rc={result.returncode}): {(result.stderr or '').strip()}",
              file=sys.stderr)
        return None
    try:
        repos = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"error: gh api events/public returned invalid JSON: {result.stdout[:200]}",
              file=sys.stderr)
        return None
    return [name for name in repos if name.startswith(f"{owner}/")]


def get_repo_languages(repo: str) -> dict[str, int]:
    """Get language breakdown for a repo."""
    full_name = repo if "/" in repo else f"{OWNER}/{repo}"
    result = run_gh_api([f"repos/{full_name}/languages"])
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def analyze_tech_trend(owner: str = OWNER) -> str | None:
    """Analyze tech trends from past week's commits.

    Returns None when the underlying API data is unavailable so the
    caller can keep previous data instead of writing a misleading summary.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    active_repos = get_active_repos(owner, since)

    if active_repos is None:
        return None
    if not active_repos:
        return "No activity this week"

    lang_counter = Counter()

    for repo in active_repos:
        languages = get_repo_languages(repo)
        lang_counter.update(languages)

    if not lang_counter:
        return None

    top = lang_counter.most_common(5)
    parts = []
    for lang, bytes_count in top:
        parts.append(f"**{lang}**")

    return f"Recently active in {len(active_repos)} repos — working with {', '.join(parts)}"


def main():
    trend = analyze_tech_trend()
    if trend is None:
        print("error: commit analysis unavailable; keeping previous README data",
              file=sys.stderr)
        sys.exit(1)
    print(trend)


if __name__ == "__main__":
    main()
