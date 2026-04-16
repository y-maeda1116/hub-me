# Dynamic GitHub Profile README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub Actions で毎日深夜0時にプロフィールカード・リポジトリステータス・コミット履歴・技術傾向を自動更新する動的 README を構築する。

**Architecture:** 単一ワークフローが profile-summary-cards Action → 3つの Python スクリプト → git commit の順に実行。Python スクリプトは標準ライブラリのみ使用し、`gh` CLI で GitHub API を呼び出す。

**Tech Stack:** Python 3.12 (stdlib only), GitHub Actions, gh CLI, vn7n24fzkq/github-profile-summary-cards

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `README.md` | テンプレート化された README |
| Create | `profile-cards/.gitkeep` | SVG 出力ディレクトリのプレースホルダ |
| Create | `.github/workflows/profile-cards.yml` | 毎日深夜0時に実行するワークフロー |
| Create | `scripts/fetch_repo_status.py` | 指定リポジトリの Release/Build status 取得 |
| Create | `scripts/analyze_commits.py` | 過去1週間のコミット解析 → 技術傾向 |
| Create | `scripts/update_readme.py` | README テンプレートの動的セクション更新 |
| Create | `tests/__init__.py` | テストパッケージ |
| Create | `tests/test_fetch_repo_status.py` | fetch_repo_status のテスト |
| Create | `tests/test_analyze_commits.py` | analyze_commits のテスト |
| Create | `tests/test_update_readme.py` | update_readme のテスト |

---

### Task 1: Create README.md Template

**Files:**
- Create: `README.md`
- Create: `profile-cards/.gitkeep`

- [ ] **Step 1: Create profile-cards directory with .gitkeep**

```bash
mkdir -p profile-cards
touch profile-cards/.gitkeep
```

- [ ] **Step 2: Create README.md template**

Create `README.md`:

```markdown
# y-maeda1116

<!-- PROFILE_CARDS -->
![Stats](profile-cards/stats.svg)
![Top Languages](profile-cards/language.svg)
![Productive Time](profile-cards/productive-time.svg)
<!-- /PROFILE_CARDS -->

## Repository Status

<!-- REPO_STATUS_TABLE -->
<!-- /REPO_STATUS_TABLE -->

## Recent Activity

<!-- RECENT_COMMITS -->
<!-- /RECENT_COMMITS -->

## Current Focus

<!-- CURRENT_FOCUS -->
<!-- /CURRENT_FOCUS -->
```

- [ ] **Step 3: Commit**

```bash
git add README.md profile-cards/.gitkeep
git commit -m "feat: add README template with dynamic section markers"
```

---

### Task 2: Create update_readme.py (Core Template Engine)

**Files:**
- Create: `scripts/update_readme.py`
- Create: `tests/__init__.py`
- Create: `tests/test_update_readme.py`

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
touch scripts/__init__.py
```

- [ ] **Step 2: Write failing test for replace_section**

Create `tests/test_update_readme.py`:

```python
"""Tests for update_readme module."""
import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from update_readme import replace_section, format_repo_status_table, format_recent_commits


class TestReplaceSection(unittest.TestCase):
    def test_replaces_content_between_tags(self):
        content = "# Title\n<!-- FOO -->old<!-- /FOO -->\n"
        result = replace_section(content, "FOO", "new")
        self.assertIn("new", result)
        self.assertNotIn("old", result)
        self.assertIn("<!-- FOO -->", result)
        self.assertIn("<!-- /FOO -->", result)

    def test_preserves_tags(self):
        content = "<!-- BAR -->x<!-- /BAR -->"
        result = replace_section(content, "BAR", "y")
        self.assertTrue(result.startswith("<!-- BAR -->"))
        self.assertTrue(result.endswith("<!-- /BAR -->"))

    def test_handles_multiline_content(self):
        content = "<!-- BAZ -->\nline1\nline2\n<!-- /BAZ -->"
        result = replace_section(content, "BAZ", "replaced")
        self.assertIn("replaced", result)
        self.assertNotIn("line1", result)

    def test_preserves_other_sections(self):
        content = "<!-- A -->1<!-- /A -->\n<!-- B -->2<!-- /B -->"
        result = replace_section(content, "A", "new_a")
        self.assertIn("new_a", result)
        self.assertIn("2", result)

    def test_no_match_returns_original(self):
        content = "<!-- A -->1<!-- /A -->"
        result = replace_section(content, "NONEXISTENT", "x")
        self.assertEqual(content, result)


class TestFormatRepoStatusTable(unittest.TestCase):
    def test_formats_json_to_markdown_table(self):
        data = [
            {"name": "repo-a", "latest_release": "v1.0", "build_status": "success"},
            {"name": "repo-b", "latest_release": "N/A", "build_status": "N/A"},
        ]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("| Repository |", table)
        self.assertIn("repo-a", table)
        self.assertIn("v1.0", table)
        self.assertIn("repo-b", table)
        self.assertIn("N/A", table)

    def test_success_icon(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success"}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("passing", table)

    def test_failure_icon(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "failure"}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("failing", table)


class TestFormatRecentCommits(unittest.TestCase):
    def test_formats_commit_list(self):
        commits = [
            {"repo": "y-maeda1116/repo-a", "message": "feat: add auth", "date": "2026-04-17"},
            {"repo": "y-maeda1116/repo-b", "message": "fix: typo", "date": "2026-04-16"},
        ]
        result = format_recent_commits(commits)
        self.assertIn("repo-a", result)
        self.assertIn("feat: add auth", result)
        self.assertIn("2026-04-17", result)

    def test_empty_commits(self):
        result = format_recent_commits([])
        self.assertIn("No recent activity", result)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_update_readme.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'update_readme'`

- [ ] **Step 4: Write update_readme.py implementation**

Create `scripts/update_readme.py`:

```python
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

    status_icons = {"success": "![passing](https://img.shields.io/badge/build-passing-brightgreen)",
                    "failure": "![failing](https://img.shields.io/badge/build-failing-red)"}

    lines = ["| Repository | Latest Release | Build Status |", "|---|---|---|"]
    for repo in repos:
        name = repo.get("name", "unknown")
        release = repo.get("latest_release", "N/A")
        build = repo.get("build_status", "N/A")
        icon = status_icons.get(build, f"![{build}](https://img.shields.io/badge/build/{build}-lightgrey)")
        lines.append(f"| [{name}](https://github.com/{owner}/{name}) | `{release}` | {icon} |")
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
        ["gh", "api", f"users/{owner}/events/public?per_page=100",
         "--jq", '[.[] | select(.type == "PushEvent") | {repo: .repo.name, message: .payload.commits[0].message, date: .created_at}][:5]'],
        capture_output=True, text=True,
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
    parser = argparse.ArgumentParser(description="Update README.md dynamic sections")
    parser.add_argument("--readme", default="README.md", help="Path to README.md")
    parser.add_argument("--repo-status-file", help="Path to JSON file from fetch_repo_status.py")
    parser.add_argument("--focus-file", help="Path to text file from analyze_commits.py")
    parser.add_argument("--dry-run", action="store_true", help="Print result without writing file")
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
            new_content = replace_section(new_content, "REPO_STATUS_TABLE", table)
        except FileNotFoundError:
            print(f"Warning: {args.repo_status_file} not found, skipping repo status", file=sys.stderr)

    try:
        commits = fetch_recent_commits(OWNER)
        commits_text = format_recent_commits(commits)
        new_content = replace_section(new_content, "RECENT_COMMITS", commits_text)
    except Exception as e:
        print(f"Warning: failed to fetch recent commits: {e}", file=sys.stderr)

    if args.focus_file:
        try:
            with open(args.focus_file, "r") as f:
                focus_text = f.read().strip()
            if focus_text:
                new_content = replace_section(new_content, "CURRENT_FOCUS", focus_text)
        except FileNotFoundError:
            print(f"Warning: {args.focus_file} not found, skipping focus", file=sys.stderr)

    if args.dry_run:
        print(new_content)
    else:
        with open(args.readme, "w") as f:
            f.write(new_content)
        print(f"Updated {args.readme}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_update_readme.py -v`
Expected: All 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/update_readme.py scripts/__init__.py tests/__init__.py tests/test_update_readme.py
git commit -m "feat: add update_readme.py with template engine and tests"
```

---

### Task 3: Create fetch_repo_status.py

**Files:**
- Create: `scripts/fetch_repo_status.py`
- Create: `tests/test_fetch_repo_status.py`

- [ ] **Step 1: Write failing test for fetch_repo_status**

Create `tests/test_fetch_repo_status.py`:

```python
"""Tests for fetch_repo_status module."""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fetch_repo_status import fetch_latest_release, fetch_build_status, fetch_repo_status


class TestFetchLatestRelease(unittest.TestCase):
    @patch("fetch_repo_status.subprocess.run")
    def test_returns_tag_on_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="v1.2.3\n")
        result = fetch_latest_release("some-repo", owner="test-user")
        self.assertEqual(result, "v1.2.3")

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_na_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = fetch_latest_release("some-repo", owner="test-user")
        self.assertEqual(result, "N/A")

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_na_on_empty(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        result = fetch_latest_release("some-repo", owner="test-user")
        self.assertEqual(result, "N/A")


class TestFetchBuildStatus(unittest.TestCase):
    @patch("fetch_repo_status.subprocess.run")
    def test_returns_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="success\n")
        result = fetch_build_status("some-repo", owner="test-user")
        self.assertEqual(result, "success")

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="failure\n")
        result = fetch_build_status("some-repo", owner="test-user")
        self.assertEqual(result, "failure")

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_na_on_no_runs(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        result = fetch_build_status("some-repo", owner="test-user")
        self.assertEqual(result, "N/A")

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_na_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = fetch_build_status("some-repo", owner="test-user")
        self.assertEqual(result, "N/A")


class TestFetchRepoStatus(unittest.TestCase):
    @patch("fetch_repo_status.fetch_build_status", return_value="success")
    @patch("fetch_repo_status.fetch_latest_release", return_value="v2.0")
    def test_returns_list_of_dicts(self, mock_release, mock_build):
        result = fetch_repo_status(["repo-a", "repo-b"], owner="test-user")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "repo-a")
        self.assertEqual(result[0]["latest_release"], "v2.0")
        self.assertEqual(result[0]["build_status"], "success")

    @patch("fetch_repo_status.fetch_build_status", return_value="N/A")
    @patch("fetch_repo_status.fetch_latest_release", return_value="N/A")
    def test_handles_all_na(self, mock_release, mock_build):
        result = fetch_repo_status(["repo-x"], owner="test-user")
        self.assertEqual(result[0]["latest_release"], "N/A")
        self.assertEqual(result[0]["build_status"], "N/A")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fetch_repo_status.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetch_repo_status'`

- [ ] **Step 3: Write fetch_repo_status.py implementation**

Create `scripts/fetch_repo_status.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fetch_repo_status.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_repo_status.py tests/test_fetch_repo_status.py
git commit -m "feat: add fetch_repo_status.py with release and build status fetching"
```

---

### Task 4: Create analyze_commits.py

**Files:**
- Create: `scripts/analyze_commits.py`
- Create: `tests/test_analyze_commits.py`

- [ ] **Step 1: Write failing test for analyze_commits**

Create `tests/test_analyze_commits.py`:

```python
"""Tests for analyze_commits module."""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from analyze_commits import detect_tech_from_files, analyze_tech_trend


class TestDetectTechFromFiles(unittest.TestCase):
    def test_detects_go(self):
        result = detect_tech_from_files(["main.go", "handler.go"])
        self.assertIn("Go", result)

    def test_detects_python(self):
        result = detect_tech_from_files(["app.py", "utils.py"])
        self.assertIn("Python", result)

    def test_detects_typescript(self):
        result = detect_tech_from_files(["index.tsx", "app.ts"])
        techs = set(result)
        self.assertIn("TypeScript", techs)

    def test_detects_terraform(self):
        result = detect_tech_from_files(["main.tf", "vars.hcl"])
        techs = set(result)
        self.assertIn("Terraform", techs)

    def test_detects_dockerfile(self):
        result = detect_tech_from_files(["Dockerfile"])
        self.assertIn("Docker", result)

    def test_unknown_extension_skipped(self):
        result = detect_tech_from_files(["readme.unknown_ext"])
        self.assertEqual(result, [])

    def test_mixed_extensions(self):
        result = detect_tech_from_files(["main.go", "app.py", "index.ts"])
        techs = set(result)
        self.assertIn("Go", techs)
        self.assertIn("Python", techs)
        self.assertIn("TypeScript", techs)

    def test_path_with_directories(self):
        result = detect_tech_from_files(["src/components/App.tsx"])
        self.assertIn("TypeScript", result)


class TestAnalyzeTechTrend(unittest.TestCase):
    @patch("analyze_commits.subprocess.run")
    def test_returns_trend_text(self, mock_run):
        events_json = json.dumps([
            {"type": "PushEvent", "repo": {"name": "y-maeda1116/repo-a"}, "created_at": "2026-04-15T00:00:00Z", "payload": {"commits": [{"message": "feat: add feature"}]}},
        ])
        languages_json = json.dumps({"Go": 5000, "Python": 3000})
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=events_json),
            MagicMock(returncode=0, stdout=languages_json),
        ]
        result = analyze_tech_trend(owner="y-maeda1116")
        self.assertIn("Go", result)
        self.assertIn("Python", result)

    @patch("analyze_commits.subprocess.run")
    def test_returns_no_activity_when_empty(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="[]")
        result = analyze_tech_trend(owner="y-maeda1116")
        self.assertEqual(result, "No activity this week")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_analyze_commits.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'analyze_commits'`

- [ ] **Step 3: Write analyze_commits.py implementation**

Create `scripts/analyze_commits.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_analyze_commits.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/analyze_commits.py tests/test_analyze_commits.py
git commit -m "feat: add analyze_commits.py with tech trend detection"
```

---

### Task 5: Create GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/profile-cards.yml`

- [ ] **Step 1: Create workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create profile-cards.yml**

Create `.github/workflows/profile-cards.yml`:

```yaml
name: Update Profile Cards

on:
  schedule:
    - cron: '0 15 * * *'
  push:
    branches: [main]
    paths-ignore:
      - 'profile-cards/**'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate Profile Summary Cards
        uses: vn7n24fzkq/github-profile-summary-cards@release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          USERNAME: ${{ github.repository_owner }}

      - name: Move generated cards to profile-cards/
        run: |
          mkdir -p profile-cards
          if [ -d profile-summary-card-output ]; then
            cp profile-summary-card-output/*.svg profile-cards/ 2>/dev/null || true
          fi

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Fetch repository status
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/fetch_repo_status.py > /tmp/repo_status.json

      - name: Analyze commits
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/analyze_commits.py > /tmp/focus.txt

      - name: Update README
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/update_readme.py \
            --repo-status-file /tmp/repo_status.json \
            --focus-file /tmp/focus.txt

      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "chore: update profile cards and README statistics"
          git push
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/profile-cards.yml
git commit -m "feat: add GitHub Actions workflow for daily profile card updates"
```

---

### Task 6: Run All Tests and Verify

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify dry-run of update_readme.py**

Run: `python scripts/update_readme.py --dry-run`
Expected: README content printed to stdout with sections intact (empty since no gh auth locally)

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git diff --staged --quiet || git commit -m "test: fix any test issues found during verification"
```
