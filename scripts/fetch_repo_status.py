#!/usr/bin/env python3
"""Fetch release and build status for all owner repositories."""
import json
import subprocess
import sys

OWNER = "y-maeda1116"


def get_all_repos(owner: str = OWNER) -> list[dict[str, str]]:
    """Get all public repos for the owner."""
    result = subprocess.run(
        ["gh", "api", f"users/{owner}/repos?per_page=100&type=owner&sort=updated",
         "--jq", "[.[] | {name: .name}]"],
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


def fetch_open_counts(repos: list[str], kind: str, owner: str = OWNER) -> dict[str, int] | None:
    """Count open items per repo via one batched Search API query.

    Multiple repo: qualifiers are OR-joined, so counting N repos costs one
    call (plus pagination) instead of N — staying far below the Search API
    rate limit that caused silent zeros when per-repo queries failed.

    kind is "is:pr" or "is:issue". Returns {repo: count} with 0 for repos
    without matches, or None on API failure so callers can keep previous
    data instead of writing zeros. Also returns None when total_count
    exceeds the Search API's 1000-result cap, where counts are unreliable.
    """
    if not repos:
        return {}
    qualifiers = [f"repo:{owner}/{name}" for name in repos] + [kind, "state:open"]
    counts = {name: 0 for name in repos}
    page = 1
    while True:
        result = subprocess.run(
            ["gh", "api",
             f"search/issues?q={'+'.join(qualifiers)}&per_page=100&page={page}",
             "--jq", "[.total_count, [.items[].repository_url]]"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return None
        try:
            total, urls = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError, TypeError):
            return None
        if total > 1000:
            return None
        for url in urls:
            name = url.rsplit("/", 1)[-1]
            if name in counts:
                counts[name] += 1
        if len(urls) < 100:
            return counts
        page += 1


def has_release_or_actions(repo: str, owner: str = OWNER) -> bool:
    """Check if repo has a release or workflow runs."""
    release = fetch_latest_release(repo, owner)
    build = fetch_build_status(repo, owner)
    return release != "N/A" or build != "N/A"


def fetch_repo_status(owner: str = OWNER) -> list[dict[str, str]]:
    """Fetch status for all repos with releases or CI. Returns list of dicts."""
    repos = get_all_repos(owner)
    if not repos:
        return []
    skip = {owner, "hub-me"}
    names = [info["name"] for info in repos if info["name"] not in skip]
    base_rows = []
    for name in names:
        release = fetch_latest_release(name, owner)
        build = fetch_build_status(name, owner)
        if release != "N/A" or build != "N/A":
            base_rows.append({
                "name": name,
                "latest_release": release,
                "build_status": build,
            })
    if not base_rows:
        return []
    targets = [row["name"] for row in base_rows]
    pr_counts = fetch_open_counts(targets, "is:pr", owner)
    issue_counts = fetch_open_counts(targets, "is:issue", owner)
    if pr_counts is None or issue_counts is None:
        return []
    return [
        {
            "name": row["name"],
            "latest_release": row["latest_release"],
            "build_status": row["build_status"],
            "open_issues": issue_counts.get(row["name"], 0),
            "open_prs": pr_counts.get(row["name"], 0),
        }
        for row in base_rows
    ]


def main():
    results = fetch_repo_status()
    if not results:
        print("error: repo status unavailable; keeping previous README data",
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
