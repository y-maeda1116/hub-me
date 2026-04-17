#!/usr/bin/env python3
"""Fetch release and build status for specified repositories."""
import json
import subprocess
import sys

OWNER = "y-maeda1116"
REPOS = [
    "Weekly-Task-Board",
    "security-base",
    "my-github-config",
    "apple-refurb-discord-notify",
]


def fetch_latest_release(repo: str, owner: str = OWNER) -> str:
    """Get latest release tag name, or 'N/A' if none exists."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/releases/latest", "--jq", ".tag_name"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "N/A"
    tag = result.stdout.strip()
    return tag if tag else "N/A"


def fetch_build_status(repo: str, owner: str = OWNER) -> str:
    """Get latest workflow run conclusion, or 'N/A' if none exists."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/actions/runs?per_page=1",
         "--jq", ".workflow_runs[0].conclusion"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "N/A"
    status = result.stdout.strip()
    return status if status else "N/A"


def fetch_repo_status(repos: list = None, owner: str = OWNER) -> list:
    """Fetch status for all repos. Returns list of dicts."""
    repos = repos or REPOS
    results = []
    for repo in repos:
        results.append({
            "name": repo,
            "latest_release": fetch_latest_release(repo, owner),
            "build_status": fetch_build_status(repo, owner),
        })
    return results


def main():
    results = fetch_repo_status()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
