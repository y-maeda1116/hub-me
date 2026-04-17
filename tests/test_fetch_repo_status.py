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
