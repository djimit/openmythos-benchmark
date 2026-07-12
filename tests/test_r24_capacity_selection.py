import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from r24_capacity_selection import CANDIDATES, select_candidate


def candidate(model_id, passed, canary_failures=1):
    return {"model_id": model_id, "evaluation": {
        "oracle_passed": passed, "canary_failures": canary_failures,
        "unique_cases": 60, "oracle_applicable": 60,
    }}


class TestR24CapacitySelection(unittest.TestCase):
    def test_selects_smallest_near_best_qualified_model(self):
        rows = [candidate(CANDIDATES[0], 15), candidate(CANDIDATES[1], 23), candidate(CANDIDATES[2], 25)]
        self.assertEqual(select_candidate(rows)["selected_model"], CANDIDATES[1])

    def test_stops_when_capacity_gain_is_too_small(self):
        rows = [candidate(CANDIDATES[0], 15), candidate(CANDIDATES[1], 20), candidate(CANDIDATES[2], 19)]
        self.assertEqual(select_candidate(rows)["status"], "stop_local_lora")


if __name__ == "__main__":
    unittest.main()
