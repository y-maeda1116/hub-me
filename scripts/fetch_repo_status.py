#!/usr/bin/env python3
"""Fetch release and build status for all owner repositories."""
import json
import subprocess
import sys

OWNER = "y-maeda1116"


def get_all_repos(owner: str = OWNER) -> list:
    """Get all public repos for the owner."""
    result = subprocess.run(
        ["gh", "api", f"users/{owner}/repos?per_page=100&type=owner&sort=updated",
         "--jq", "[.[] | {name: .name, has_actions: .has_wiki}]"],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


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


def has_release_or_actions(repo: str, owner: str = OWNER) -> bool:
    """Check if repo has a release or workflow runs."""
    release = fetch_latest_release(repo, owner)
    build = fetch_build_status(repo, owner)
    return release != "N/A" or build != "N/A"


def fetch_repo_status(owner: str = OWNER) -> list:
    """Fetch status for all repos with releases or CI. Returns list of dicts."""
    repos = get_all_repos(owner)
    if not repos:
        return []
    results = []
    for repo_info in repos:
        name = repo_info["name"]
        release = fetch_latest_release(name, owner)
        build = fetch_build_status(name, owner)
        if release != "N/A" or build != "N/A":
            results.append({
                "name": name,
                "latest_release": release,
                "build_status": build,
            })
    return results


def main():
    results = fetch_repo_status()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
