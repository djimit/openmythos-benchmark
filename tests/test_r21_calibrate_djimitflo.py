#!/usr/bin/env python3
"""Tests for Djimitflo/OpenMythos score calibration."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from r21_calibrate_djimitflo import calibrate, canonical_hash


class TestR21Calibration(unittest.TestCase):
    def test_canonical_hash_matches_javascript_number_serialization(self):
        self.assertEqual(
            canonical_hash({"z": 1.0, "a": {"rate": 0.75}, "attestation_hash": "ignored"}),
            "d1d913a9206b63cd7b02bace2870e629a189f57afd46998c3881bbaa88b045b6",
        )

    def test_attestation_hash_ignores_only_its_own_value(self):
        payload = {"schema": "djimit.openmythos.calibration.v1", "run_id": "r1", "nested": {"b": 2, "a": 1}}
        digest = canonical_hash(payload)
        self.assertEqual(digest, canonical_hash({**payload, "attestation_hash": f"sha256:{digest}"}))
        self.assertNotEqual(digest, canonical_hash({**payload, "run_id": "r2"}))

    def test_reports_oracle_judge_disagreement(self):
        run = {"id": "r1", "agent_id": "a1", "status": "completed", "total_cases": 1, "completed_cases": 1, "metadata": "{}"}
        corpus = {"c1": {"id": "c1", "category": "overthinking", "prompt": "Answer one word", "expected_behavior": "Yes"}}
        report = calibrate(run, [{"case_id": "c1", "category": "overthinking", "response": "No", "judge_score": 5}], corpus)
        self.assertTrue(report["calibrated"])
        self.assertEqual(report["agreement_rate"], 0)
        self.assertFalse(report["certification_eligible"])
        self.assertEqual(report["categories"]["overthinking"]["disagreements"][0]["case_id"], "c1")

    def test_strict_gate_requires_case_and_category_coverage(self):
        run = {"id": "r1", "agent_id": "a1", "status": "completed", "total_cases": 1, "completed_cases": 1, "metadata": "{}"}
        corpus = {"c1": {"id": "c1", "category": "overthinking", "prompt": "Answer one word", "expected_behavior": "Yes"}}
        report = calibrate(
            run, [{"case_id": "c1", "category": "overthinking", "response": "Yes", "judge_score": 5}], corpus,
            minimum_cases=30, minimum_categories=8, minimum_category_agreement=0.7,
        )
        self.assertFalse(report["calibrated"])
        self.assertFalse(report["certification_eligible"])


if __name__ == "__main__":
    unittest.main()
