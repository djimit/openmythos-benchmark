#!/usr/bin/env python3
"""Tests for the draft skill-lifecycle admission gate and its oracle anchors."""

import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import skill_lifecycle_gate as gate


class TestSkillLifecycleGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(gate.SCHEMA_PATH.read_text())
        cls.cases = [json.loads(line) for line in gate.CASES_PATH.read_text().splitlines() if line.strip()]
        cls.anchors = json.loads(gate.ANCHORS_PATH.read_text())

    def errors(self, anchors=None):
        return gate.check(self.cases, anchors or self.anchors, self.schema)

    def test_repository_drafts_pass(self):
        self.assertEqual(self.errors(), [])

    def test_exact_label_drafts_use_exact_scalar(self):
        types = {anchor["oracle_type"] for anchor in self.anchors["anchors"].values()}
        self.assertEqual(types, {"exact_scalar"})

    def test_rejects_substring_oracle_for_exact_label_contract(self):
        anchors = copy.deepcopy(self.anchors)
        anchors["anchors"]["skill-lifecycle-001"]["oracle_type"] = "required_text"
        self.assertIn("skill-lifecycle-001: invalid deterministic oracle anchor", self.errors(anchors))

    def test_rejects_label_outside_the_prompt_contract(self):
        anchors = copy.deepcopy(self.anchors)
        anchors["anchors"]["skill-lifecycle-001"]["expected"] = "BLOCK"
        self.assertIn("skill-lifecycle-001: anchor label is not one of the prompt's exact labels", self.errors(anchors))

    def test_rejects_label_that_is_only_a_substring_of_the_gold_decision(self):
        # DO_NOT_SELECT contains SELECT and both are allowed labels, but SELECT is not the gold decision.
        anchors = copy.deepcopy(self.anchors)
        anchors["anchors"]["skill-lifecycle-010"]["expected"] = "SELECT"
        self.assertIn("skill-lifecycle-010: anchor label does not lead expected_behavior", self.errors(anchors))


if __name__ == "__main__":
    unittest.main()
