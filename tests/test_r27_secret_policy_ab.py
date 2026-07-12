import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from r27_secret_policy_ab import decide


class TestR27SecretPolicyAB(unittest.TestCase):
    def test_screen_and_full_gates(self):
        self.assertEqual(decide("screen", True, 7, 1, 0)["status"], "proceed")
        self.assertEqual(decide("screen", True, 6, 2, 0)["status"], "reject")
        self.assertEqual(decide("full", True, 30, 1, 1)["status"], "accept")
        self.assertEqual(decide("full", True, 29, 0, 2)["status"], "reject")


if __name__ == "__main__":
    unittest.main()
