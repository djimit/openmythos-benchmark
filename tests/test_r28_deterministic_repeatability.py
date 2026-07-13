import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from r28_deterministic_repeatability import decide


class TestR28DeterministicRepeatability(unittest.TestCase):
    def test_decision_requires_exact_and_oracle_stability(self):
        self.assertEqual(decide(True, 8, True, True)["status"], "pass")
        self.assertEqual(decide(True, 8, False, True)["reasons"], ["response-instability"])
        self.assertEqual(decide(True, 8, True, False)["reasons"], ["oracle-instability"])


if __name__ == "__main__":
    unittest.main()
