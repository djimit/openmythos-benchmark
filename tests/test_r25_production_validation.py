import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from r25_production_validation import decide, percentile


class TestR25ProductionValidation(unittest.TestCase):
    def test_quality_and_canary_gates(self):
        self.assertEqual(decide(True, 60, 31, 1, 8)["status"], "qualified")
        self.assertEqual(decide(True, 60, 30, 2, 8)["status"], "not_qualified")

    def test_nearest_rank_percentile(self):
        self.assertEqual(percentile([10, 20, 30, 40], 0.95), 40)


if __name__ == "__main__":
    unittest.main()
