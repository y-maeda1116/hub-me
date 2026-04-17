#!/usr/bin/env python3
"""Analyze past week's commits to detect technology trends."""
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

OWNER = "y-maeda1116"

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


def detect_tech_from_files(files: list) -> list:
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


def get_active_repos(owner: str, since: str) -> list:
    """Get repos with push events since given date."""
    result = subprocess.run(
        ["gh", "api", f"users/{owner}/events/public?per_page=100",
         "--jq", f'[.[] | select(.type == "PushEvent" and .created_at >= "{since}") | .repo.name] | unique'],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def get_repo_languages(repo: str) -> dict:
    """Get language breakdown for a repo."""
    full_name = repo if "/" in repo else f"{OWNER}/{repo}"
    result = subprocess.run(
        ["gh", "api", f"repos/{full_name}/languages"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def analyze_tech_trend(owner: str = OWNER) -> str:
    """Analyze tech trends from past week's commits."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    active_repos = get_active_repos(owner, since)

    if not active_repos:
        return "No activity this week"

    lang_counter = Counter()
    total_commits = 0

    for repo in active_repos:
        languages = get_repo_languages(repo)
        lang_counter.update(languages)
        total_commits += 1

    if not lang_counter:
        return "No activity this week"

    top = lang_counter.most_common(5)
    parts = []
    for lang, bytes_count in top:
        parts.append(f"**{lang}**")

    return f"Recently active in {len(active_repos)} repos — working with {', '.join(parts)}"


def main():
    print(analyze_tech_trend())


if __name__ == "__main__":
    main()
