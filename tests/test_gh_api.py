import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from gh_api import run_gh_api


class TestRunGhApi(unittest.TestCase):
    @patch("gh_api.time.sleep")
    @patch("gh_api.subprocess.run")
    def test_retries_transient_failure_then_succeeds(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="gh: secondary rate limit (HTTP 403)"),
            MagicMock(returncode=0, stdout="ok"),
        ]
        result = run_gh_api(["users/x"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(60)

    @patch("gh_api.time.sleep")
    @patch("gh_api.subprocess.run")
    def test_does_not_retry_not_found(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="gh: Not Found (HTTP 404)")
        result = run_gh_api(["repos/x/y/releases/latest"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(mock_run.call_count, 1)
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
