#!/usr/bin/env python3
"""Tests for Djimitflo/OpenMythos score calibration."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from r21_calibrate_djimitflo import calibrate


class TestR21Calibration(unittest.TestCase):
    def test_reports_oracle_judge_disagreement(self):
        run = {"id": "r1", "agent_id": "a1", "status": "completed", "total_cases": 1, "completed_cases": 1, "metadata": "{}"}
        corpus = {"c1": {"id": "c1", "category": "overthinking", "prompt": "Answer one word", "expected_behavior": "Yes"}}
        report = calibrate(run, [{"case_id": "c1", "category": "overthinking", "response": "No", "judge_score": 5}], corpus)
        self.assertTrue(report["calibrated"])
        self.assertEqual(report["agreement_rate"], 0)
        self.assertFalse(report["certification_eligible"])
        self.assertEqual(report["categories"]["overthinking"]["disagreements"][0]["case_id"], "c1")


if __name__ == "__main__":
    unittest.main()
