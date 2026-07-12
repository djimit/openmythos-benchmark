#!/usr/bin/env python3
"""Tests for the R21 holdout manifest."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from r21_holdout import CONFIRMATORY_CASES, build


class TestR21Holdout(unittest.TestCase):
    def test_holdout_is_large_diverse_unique_and_train_disjoint(self):
        rows = build()
        ids = {row["metadata"]["case_id"] for row in rows}
        categories = {row["metadata"]["category"] for row in rows}
        self.assertEqual(len(rows), len(ids))
        self.assertGreaterEqual(len(ids), 30)
        self.assertGreaterEqual(len(categories), 8)

    def test_confirmatory_fold_is_disjoint(self):
        development = build()
        confirmatory = build(cases=CONFIRMATORY_CASES, split="confirmatory_holdout")
        development_ids = {row["metadata"]["case_id"] for row in development}
        confirmatory_ids = {row["metadata"]["case_id"] for row in confirmatory}
        self.assertFalse(development_ids & confirmatory_ids)
        self.assertEqual(len(confirmatory_ids), 30)
        self.assertGreaterEqual(len({row["metadata"]["category"] for row in confirmatory}), 8)


if __name__ == "__main__":
    unittest.main()
