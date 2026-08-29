#!/usr/bin/env python3
"""Fail-closed promotion pipeline contracts."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gate_pipeline import run_pipeline, run_promotion_gate


class TestGatePipeline(unittest.TestCase):
    def test_promotion_rejects_traces_not_bound_to_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.jsonl"
            corpus.write_text(json.dumps({"id": "canonical-001"}) + "\n")
            trace_dirs = []
            for index in range(2):
                trace_dir = root / f"run-{index}"
                trace_dir.mkdir()
                (trace_dir / "judged_model.jsonl").write_text(
                    json.dumps({"case_id": "invented-001", "judge_score": 5}) + "\n"
                )
                trace_dirs.append(trace_dir)

            passed, detail = run_promotion_gate(trace_dirs, corpus)
            self.assertFalse(passed)
            self.assertIn("certified corpus", detail["reason"])

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
