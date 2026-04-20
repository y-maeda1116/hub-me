"""Tests for fetch_repo_status module."""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fetch_repo_status import fetch_latest_release, fetch_build_status, fetch_repo_status, get_all_repos


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
    @patch("fetch_repo_status.get_all_repos")
    def test_filters_repos_with_data(self, mock_get_repos, mock_release, mock_build):
        mock_get_repos.return_value = [{"name": "repo-a"}, {"name": "repo-b"}]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "repo-a")

    @patch("fetch_repo_status.fetch_build_status", return_value="N/A")
    @patch("fetch_repo_status.fetch_latest_release", return_value="N/A")
    @patch("fetch_repo_status.get_all_repos")
    def test_excludes_repos_without_data(self, mock_get_repos, mock_release, mock_build):
        mock_get_repos.return_value = [{"name": "empty-repo"}]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(result, [])

    @patch("fetch_repo_status.fetch_build_status", return_value="N/A")
    @patch("fetch_repo_status.fetch_latest_release", return_value="v1.0")
    @patch("fetch_repo_status.get_all_repos")
    def test_includes_repo_with_release_only(self, mock_get_repos, mock_release, mock_build):
        mock_get_repos.return_value = [{"name": "released-repo"}]
        result = fetch_repo_status(owner="test-user")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["latest_release"], "v1.0")


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


if __name__ == "__main__":
    unittest.main()
