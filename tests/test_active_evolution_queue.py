#!/usr/bin/env python3
"""Contract tests for DjimitFlo active-evolution campaigns."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from active_evolution_queue import batch_goals, build_goal_batch


class TestActiveEvolutionQueue(unittest.TestCase):
    def test_splits_campaign_into_bounded_dependency_preserving_waves(self):
        goals = [
            {
                "key": f"goal-{index}",
                "depends_on": [f"goal-{index - 1}"] if index else [],
                "api": {"body": {"objective": f"Goal {index}", "acceptance_criteria": ["verified"]}},
            }
            for index in range(5)
        ]
        batch = build_goal_batch(
            {"generated_at": "2026-09-07T00:00:00Z", "inputs": {}, "djimitflo_goals": goals},
            "campaign-1",
        )

        self.assertEqual(batch["schema"], "djimit.openmythos.goal.v1")
        self.assertEqual([wave["wave_id"] for wave in batch["waves"]], ["wave-1", "wave-2"])
        self.assertEqual([len(wave["ordered_goals"]) for wave in batch["waves"]], [3, 2])
        self.assertEqual(batch_goals(batch), goals)
        self.assertEqual(batch["waves"][1]["ordered_goals"][0]["depends_on"], ["goal-2"])


if __name__ == "__main__":
    unittest.main()
