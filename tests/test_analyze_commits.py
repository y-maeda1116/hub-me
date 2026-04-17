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
