#!/usr/bin/env python3
"""Tests for the R20 LoRA/SFT pilot gate."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from r20_lora_sft_pilot import build_report, select_device, valid_dpo, valid_sft


class TestR20Pilot(unittest.TestCase):
    def test_schema_helpers(self):
        self.assertTrue(valid_sft({"messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]}))
        self.assertTrue(valid_dpo({"prompt": "x", "chosen": "y", "rejected": "z"}))
        self.assertFalse(valid_dpo({"prompt": "x", "chosen": "y", "rejected": "y"}))

    def test_case_overlap_blocks_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sft = root / "sft.jsonl"
            dpo = root / "dpo.jsonl"
            holdout = root / "holdout.jsonl"
            sft.write_text(json.dumps({"messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}], "metadata": {"case_id": "c1"}}) + "\n")
            dpo.write_text(json.dumps({"prompt": "x", "chosen": "y", "rejected": "z", "metadata": {"case_id": "c1"}}) + "\n")
            holdout.write_text(json.dumps({"prompt": "x", "chosen": "y", "rejected": "z", "metadata": {"case_id": "c1"}}) + "\n")
            report = build_report(sft, dpo, holdout)
            self.assertIn("train-holdout-case-overlap", report["training"]["blockers"])

    def test_duplicate_sft_case_blocks_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sft = root / "sft.jsonl"
            dpo = root / "dpo.jsonl"
            holdout = root / "holdout.jsonl"
            row = {"messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}], "metadata": {"case_id": "c1", "category": "a"}}
            sft.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
            dpo.write_text("")
            holdout.write_text("")
            self.assertIn("duplicate-sft-case", build_report(sft, dpo, holdout)["training"]["blockers"])

    def test_device_selection_prefers_cuda(self):
        class Available:
            @staticmethod
            def is_available(): return True
        class Unavailable:
            @staticmethod
            def is_available(): return False
        class Torch:
            cuda = Available()
            backends = type("Backends", (), {"mps": Unavailable()})()
            float16 = "fp16"
            float32 = "fp32"
        self.assertEqual(select_device(Torch)["device"], "cuda")


if __name__ == "__main__":
    unittest.main()
