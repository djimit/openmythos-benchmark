#!/usr/bin/env python3
"""Tests for the R22 oracle-first calibration artifacts."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from r22_oracle_calibration import DEVELOPMENT_PATHS, build_holdout, export_anchors, load_rows


class TestR22OracleCalibration(unittest.TestCase):
    def test_fresh_holdout_is_fully_anchored(self):
        rows = build_holdout()
        payload = export_anchors([("r22", rows)])
        self.assertEqual(len(rows), 30)
        self.assertEqual(len({row["metadata"]["case_id"] for row in rows}), 30)
        self.assertEqual(len({row["metadata"]["category"] for row in rows}), 8)
        self.assertEqual(len(payload["anchors"]), 30)
        self.assertEqual(payload["skipped"], [])

    def test_development_and_holdout_manifests_are_fully_anchored(self):
        manifests = [(path.name, load_rows(path)) for path in DEVELOPMENT_PATHS]
        manifests.append(("r22", build_holdout()))
        payload = export_anchors(manifests)
        self.assertEqual(len(payload["anchors"]), 90)
        self.assertEqual(payload["skipped"], [])


if __name__ == "__main__":
    unittest.main()
