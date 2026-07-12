import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from r23_adapter_ab import decide, validate_inputs


class TestR23AdapterAB(unittest.TestCase):
    def test_validation_uses_actual_sft_training_set(self):
        from tempfile import TemporaryDirectory
        import json

        with TemporaryDirectory() as directory:
            root = Path(directory)
            sft = root / "sft.jsonl"
            holdout = root / "holdout.jsonl"
            sft.write_text(json.dumps({"metadata": {"case_id": "train"}}) + "\n")
            holdout.write_text("".join(json.dumps({
                "prompt": "p", "metadata": {"case_id": f"c{i}", "category": f"cat{i % 8}"},
            }) + "\n" for i in range(30)))
            self.assertEqual(validate_inputs(sft, holdout), ([], 8))

    def test_promotion_requires_two_wins_without_regression(self):
        base = {
            "unique_cases": 30, "oracle_applicable": 30, "over_refusal": 1,
            "results": [{"case_id": f"c{i}", "oracle_pass": i < 10} for i in range(30)],
        }
        adapter = {
            "unique_cases": 30, "oracle_applicable": 30, "over_refusal": 1,
            "results": [{"case_id": f"c{i}", "oracle_pass": i < 12} for i in range(30)],
        }
        self.assertEqual(decide(base, adapter, 8)["status"], "promote")
        adapter["results"][0]["oracle_pass"] = False
        self.assertEqual(decide(base, adapter, 8)["status"], "reject")


if __name__ == "__main__":
    unittest.main()
