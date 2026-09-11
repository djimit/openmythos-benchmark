import tempfile
import unittest
from pathlib import Path

from worldlab.social_learning import replay_campaign


class SocialLearningReplayTests(unittest.TestCase):
    def test_replay_is_exact_but_does_not_invent_causality(self) -> None:
        payload = {
            "schema": "djimit.social-learning-campaign.worldlab-input.v1",
            "campaign_id": "social-confirmatory-test",
            "report_hash": "sha256:report",
            "pairs": [{
                "thread_id": "social:1", "agent_id": "agent-a", "peer_agent_id": "agent-b",
                "baseline_message_id": "baseline", "peer_message_id": "peer", "learning_message_id": "learning",
                "reflection_id": "reflection", "baseline_hash": "sha256:baseline", "peer_hash": "sha256:peer",
                "learning_hash": "sha256:learning", "effect_scope": "isolated",
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            result = replay_campaign(payload, "worldlab-commit", Path(directory))
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["trajectories"], 1)
            self.assertFalse(result["causal_claim_supported"])
            self.assertTrue(result["trajectory_index"][0]["replay_exact"])
            self.assertEqual(len(list(Path(directory).glob("*.jsonl"))), 1)

    def test_replay_fails_closed_on_non_isolated_or_self_peer_input(self) -> None:
        payload = {
            "schema": "djimit.social-learning-campaign.worldlab-input.v1", "campaign_id": "bad", "pairs": [{
                "thread_id": "social:1", "agent_id": "same", "peer_agent_id": "same",
                "baseline_hash": "a", "peer_hash": "b", "learning_hash": "c", "effect_scope": "production",
            }],
        }
        result = replay_campaign(payload, "worldlab-commit")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["trajectories"], 0)


if __name__ == "__main__":
    unittest.main()
