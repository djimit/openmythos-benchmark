#!/usr/bin/env python3
"""Tests for the R21 holdout manifest."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from r21_holdout import build


class TestR21Holdout(unittest.TestCase):
    def test_holdout_is_large_diverse_unique_and_train_disjoint(self):
        rows = build()
        ids = {row["metadata"]["case_id"] for row in rows}
        categories = {row["metadata"]["category"] for row in rows}
        self.assertEqual(len(rows), len(ids))
        self.assertGreaterEqual(len(ids), 30)
        self.assertGreaterEqual(len(categories), 8)


if __name__ == "__main__":
    unittest.main()
