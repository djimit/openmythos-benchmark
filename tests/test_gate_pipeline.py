#!/usr/bin/env python3
"""Fail-closed promotion pipeline contracts."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gate_pipeline import run_pipeline


class TestGatePipeline(unittest.TestCase):
    def test_caller_supplied_corpus_cannot_supply_its_own_certification(self):
        result = run_pipeline(
            candidate_traces=[Path("candidate.jsonl")],
            baseline_traces=[Path("baseline.jsonl")],
            corpus=Path("caller-controlled/corpus.jsonl"),
            gates=["promotion"],
        )
        self.assertEqual(result["overall"], "rejected")
        self.assertIn("canonical corpus", result["gates"][0]["errors"][0])

    def test_uncertified_corpus_cannot_reach_promotion(self):
        result = run_pipeline(
            candidate_traces=[Path("candidate.jsonl")],
            baseline_traces=[Path("baseline.jsonl")],
            corpus=REPO_ROOT / "cases" / "corpus.jsonl",
            gates=["promotion"],
        )
        self.assertEqual(result["overall"], "rejected")
        self.assertEqual(result["stopped_at"], "corpus_manifest")


if __name__ == "__main__":
    unittest.main()
