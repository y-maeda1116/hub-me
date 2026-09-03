"""Tests for update_readme module."""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from update_readme import (
    replace_section,
    format_repo_status_table,
    format_recent_commits,
    fetch_recent_commits,
    main,
)


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
            {"name": "repo-a", "latest_release": "v1.0", "build_status": "success", "open_issues": 3, "open_prs": 1},
            {"name": "repo-b", "latest_release": "N/A", "build_status": "N/A", "open_issues": 0, "open_prs": 0},
        ]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("| Repository |", table)
        self.assertIn("repo-a", table)
        self.assertIn("v1.0", table)
        self.assertIn("repo-b", table)
        self.assertIn("N/A", table)

    def test_includes_issues_and_prs_columns(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success", "open_issues": 5, "open_prs": 2}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("Open Issues", table)
        self.assertIn("Open PRs", table)

    def test_renders_issues_and_prs_counts(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success", "open_issues": 7, "open_prs": 4}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("7", table)
        self.assertIn("4", table)

    def test_issues_count_links_to_issues_page(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success", "open_issues": 7, "open_prs": 0}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn(
            '[7](https://github.com/y-maeda1116/repo/issues)',
            table,
        )

    def test_prs_count_links_to_pulls_page(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success", "open_issues": 0, "open_prs": 4}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn(
            '[4](https://github.com/y-maeda1116/repo/pulls)',
            table,
        )

    def test_zero_counts_still_linked(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success", "open_issues": 0, "open_prs": 0}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("repo/issues", table)
        self.assertIn("repo/pulls", table)

    def test_defaults_missing_counts_to_zero(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success"}]
        table = format_repo_status_table(json.dumps(data), "y-maeda1116")
        self.assertIn("0", table)

    def test_success_icon(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "success", "open_issues": 0, "open_prs": 0}]
        table = format_repo_status_table(json.dumps(data), "y-medaed1116")
        self.assertIn("passing", table)

    def test_failure_icon(self):
        data = [{"name": "repo", "latest_release": "v1", "build_status": "failure", "open_issues": 0, "open_prs": 0}]
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


class TestFetchRecentCommits(unittest.TestCase):
    @patch("update_readme.subprocess.run")
    def test_returns_commits_on_success(self, mock_run):
        commits_json = json.dumps([
            {"repo": "y-maeda1116/repo-a", "message": "feat: x", "date": "2026-08-20T00:00:00Z"},
        ])
        mock_run.return_value = MagicMock(returncode=0, stdout=commits_json)
        result = fetch_recent_commits("y-maeda1116")
        self.assertEqual(len(result), 1)

    @patch("update_readme.time.sleep")
    @patch("update_readme.subprocess.run")
    def test_returns_none_on_error(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(fetch_recent_commits("y-maeda1116"))

    @patch("update_readme.subprocess.run")
    def test_returns_none_on_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        self.assertIsNone(fetch_recent_commits("y-maeda1116"))

    @patch("update_readme.time.sleep")
    @patch("update_readme.subprocess.run")
    def test_retries_transient_failure_then_succeeds(self, mock_run, mock_sleep):
        commits_json = json.dumps([
            {"repo": "y-maeda1116/repo-a", "message": "feat: x", "date": "2026-08-20T00:00:00Z"},
        ])
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="secondary rate limit"),
            MagicMock(returncode=0, stdout=commits_json),
        ]
        result = fetch_recent_commits("y-maeda1116")
        self.assertEqual(len(result), 1)
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(60)

    @patch("update_readme.time.sleep")
    @patch("update_readme.subprocess.run")
    def test_returns_none_after_exhausting_retries(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(fetch_recent_commits("y-maeda1116"))
        self.assertEqual(mock_run.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


class TestMain(unittest.TestCase):
    def test_exits_nonzero_and_keeps_file_when_commits_fetch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = os.path.join(tmp, "README.md")
            with open(readme, "w") as f:
                f.write("<!-- RECENT_COMMITS -->\nold content\n<!-- /RECENT_COMMITS -->\n")
            with patch("update_readme.fetch_recent_commits", return_value=None), \
                 patch("sys.argv", ["prog", "--readme", readme]):
                with self.assertRaises(SystemExit) as ctx:
                    main()
            self.assertEqual(ctx.exception.code, 1)
            with open(readme) as f:
                self.assertIn("old content", f.read())


if __name__ == "__main__":
    unittest.main()
