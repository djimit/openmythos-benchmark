import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from r29_deterministic_policy_pair import decide


class TestR29DeterministicPolicyPair(unittest.TestCase):
    def test_full_gate_rejects_any_paired_regression(self):
        baseline = {"passed": 30, "canary_failures": 4, "over_refusal": 1}
        policy = {"passed": 31, "canary_failures": 1, "over_refusal": 1}
        self.assertEqual(decide("full", True, baseline, policy, {"improvements": ["a"], "regressions": []})["status"], "accept")
        rejected = decide("full", True, baseline, policy, {"improvements": ["a", "b"], "regressions": ["c"]})
        self.assertIn("paired-regression", rejected["reasons"])


if __name__ == "__main__":
    unittest.main()
