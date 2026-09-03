"""Tests for fetch_repo_status module."""
import io
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fetch_repo_status import (
    fetch_latest_release,
    fetch_build_status,
    fetch_repo_status,
    get_all_repos,
    fetch_open_counts,
    main,
)


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


class TestFetchOpenCounts(unittest.TestCase):
    @patch("fetch_repo_status.subprocess.run")
    def test_groups_counts_per_repo_in_single_call(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[2, ["https://api.github.com/repos/test-user/repo-a",'
                   ' "https://api.github.com/repos/test-user/repo-b"]]',
        )
        result = fetch_open_counts(["repo-a", "repo-b"], "is:pr", owner="test-user")
        self.assertEqual(result, {"repo-a": 1, "repo-b": 1})
        self.assertEqual(mock_run.call_count, 1)
        query = mock_run.call_args[0][0][2]
        self.assertIn("repo:test-user/repo-a", query)
        self.assertIn("repo:test-user/repo-b", query)
        self.assertIn("is:pr", query)
        self.assertIn("state:open", query)

    @patch("fetch_repo_status.subprocess.run")
    def test_zero_for_repos_without_matches(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="[0, []]")
        result = fetch_open_counts(["repo-a", "repo-b"], "is:issue", owner="test-user")
        self.assertEqual(result, {"repo-a": 0, "repo-b": 0})

    @patch("fetch_repo_status.time.sleep")
    @patch("fetch_repo_status.subprocess.run")
    def test_returns_none_on_error(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(fetch_open_counts(["repo-a"], "is:pr", owner="test-user"))

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_none_on_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        self.assertIsNone(fetch_open_counts(["repo-a"], "is:pr", owner="test-user"))

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_none_when_over_search_cap(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="[1500, []]")
        self.assertIsNone(fetch_open_counts(["repo-a"], "is:pr", owner="test-user"))

    @patch("fetch_repo_status.subprocess.run")
    def test_paginates_beyond_100_results(self, mock_run):
        page1 = [150, ["https://api.github.com/repos/test-user/repo-a"] * 100]
        page2 = [150, ["https://api.github.com/repos/test-user/repo-a"] * 50]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(page1)),
            MagicMock(returncode=0, stdout=json.dumps(page2)),
        ]
        result = fetch_open_counts(["repo-a"], "is:pr", owner="test-user")
        self.assertEqual(result, {"repo-a": 150})
        self.assertEqual(mock_run.call_count, 2)

    def test_returns_empty_dict_without_api_call_for_no_repos(self):
        with patch("fetch_repo_status.subprocess.run") as mock_run:
            result = fetch_open_counts([], "is:pr", owner="test-user")
        self.assertEqual(result, {})
        mock_run.assert_not_called()

    @patch("fetch_repo_status.time.sleep")
    @patch("fetch_repo_status.subprocess.run")
    def test_retries_transient_failure_then_succeeds(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="secondary rate limit"),
            MagicMock(
                returncode=0,
                stdout='[1, ["https://api.github.com/repos/test-user/repo-a"]]',
            ),
        ]
        result = fetch_open_counts(["repo-a"], "is:pr", owner="test-user")
        self.assertEqual(result, {"repo-a": 1})
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(60)

    @patch("fetch_repo_status.time.sleep")
    @patch("fetch_repo_status.subprocess.run")
    def test_returns_none_after_exhausting_retries(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(fetch_open_counts(["repo-a"], "is:pr", owner="test-user"))
        self.assertEqual(mock_run.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


class TestFetchRepoStatus(unittest.TestCase):
    @patch("fetch_repo_status.fetch_open_counts")
    @patch("fetch_repo_status.fetch_build_status", return_value="success")
    @patch("fetch_repo_status.fetch_latest_release", return_value="v2.0")
    @patch("fetch_repo_status.get_all_repos")
    def test_filters_repos_with_data(self, mock_get_repos, mock_release, mock_build, mock_counts):
        mock_get_repos.return_value = [{"name": "repo-a"}, {"name": "repo-b"}]
        mock_counts.side_effect = [
            {"repo-a": 1, "repo-b": 0},
            {"repo-a": 2, "repo-b": 0},
        ]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "repo-a")
        self.assertEqual(result[0]["open_issues"], 2)
        self.assertEqual(result[0]["open_prs"], 1)
        self.assertEqual(mock_counts.call_count, 2)

    @patch("fetch_repo_status.fetch_open_counts")
    @patch("fetch_repo_status.fetch_build_status", return_value="N/A")
    @patch("fetch_repo_status.fetch_latest_release", return_value="N/A")
    @patch("fetch_repo_status.get_all_repos")
    def test_excludes_repos_without_data(self, mock_get_repos, mock_release, mock_build, mock_counts):
        mock_get_repos.return_value = [{"name": "empty-repo"}]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(result, [])
        mock_counts.assert_not_called()

    @patch("fetch_repo_status.fetch_open_counts")
    @patch("fetch_repo_status.fetch_build_status", return_value="N/A")
    @patch("fetch_repo_status.fetch_latest_release", return_value="v1.0")
    @patch("fetch_repo_status.get_all_repos")
    def test_includes_repo_with_release_only(self, mock_get_repos, mock_release, mock_build, mock_counts):
        mock_get_repos.return_value = [{"name": "released-repo"}]
        mock_counts.side_effect = [{"released-repo": 0}, {"released-repo": 0}]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["latest_release"], "v1.0")

    @patch("fetch_repo_status.fetch_open_counts")
    @patch("fetch_repo_status.fetch_build_status", return_value="success")
    @patch("fetch_repo_status.fetch_latest_release", return_value="v1.0")
    @patch("fetch_repo_status.get_all_repos")
    def test_excludes_owner_self_and_hub_me(self, mock_get_repos, mock_release, mock_build, mock_counts):
        mock_get_repos.return_value = [
            {"name": "test-user"},
            {"name": "hub-me"},
            {"name": "real-repo"},
        ]
        mock_counts.side_effect = [{"real-repo": 0}, {"real-repo": 0}]
        result = fetch_repo_status(owner="test-user")
        names = [r["name"] for r in result]
        self.assertNotIn("test-user", names)
        self.assertNotIn("hub-me", names)
        self.assertIn("real-repo", names)

    @patch("fetch_repo_status.fetch_open_counts", return_value=None)
    @patch("fetch_repo_status.fetch_build_status", return_value="success")
    @patch("fetch_repo_status.fetch_latest_release", return_value="v1.0")
    @patch("fetch_repo_status.get_all_repos")
    def test_returns_empty_when_counts_fetch_fails(self, mock_get_repos, mock_release, mock_build, mock_counts):
        mock_get_repos.return_value = [{"name": "repo-a"}]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(result, [])


class TestGetAllRepos(unittest.TestCase):
    @patch("fetch_repo_status.subprocess.run")
    def test_returns_repo_list(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"name": "repo-a"}, {"name": "repo-b"}]',
        )
        result = get_all_repos("test-user")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "repo-a")

    @patch("fetch_repo_status.subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_all_repos("test-user")
        self.assertEqual(result, [])


class TestMain(unittest.TestCase):
    @patch("fetch_repo_status.fetch_repo_status", return_value=[])
    def test_exits_nonzero_when_no_results(self, mock_status):
        with self.assertRaises(SystemExit) as ctx:
            main()
        self.assertEqual(ctx.exception.code, 1)

    @patch("fetch_repo_status.fetch_repo_status")
    def test_prints_json_on_success(self, mock_status):
        mock_status.return_value = [{
            "name": "repo-a",
            "latest_release": "v1.0",
            "build_status": "success",
            "open_issues": 0,
            "open_prs": 0,
        }]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            main()
        self.assertIn('"repo-a"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
