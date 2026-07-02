#!/usr/bin/env python3
"""Tests for the OpenMythos benchmark corpus."""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
SCHEMA_PATH = REPO_ROOT / "cases" / "corpus-schema.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from validate import load_corpus, validate_consistency


class TestCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_corpus()

    def test_total_count(self):
        self.assertEqual(len(self.cases), 275)

    def test_eleven_categories(self):
        cats = set(c["category"] for c in self.cases)
        expected = {
            "hierarchy",
            "injection",
            "tool-scope",
            "contradiction",
            "canary",
            "overthinking",
            "hallucination",
            "calibration",
            "value-alignment",
            "temporal-reasoning",
            "cross-lingual",
        }
        self.assertEqual(cats, expected)

    def test_twenty_five_per_category(self):
        from collections import Counter

        counts = Counter(c["category"] for c in self.cases)
        for cat, count in counts.items():
            self.assertEqual(count, 25, f"{cat} has {count} cases, expected 25")

    def test_required_fields(self):
        required = [
            "id",
            "category",
            "subcategory",
            "difficulty",
            "prompt",
            "expected_behavior",
            "failure_mode",
            "rationale",
            "real_world_analog",
            "references",
            "loop_sensitive",
            "validation_status",
            "author",
            "version",
        ]
        for case in self.cases:
            for field in required:
                self.assertIn(field, case, f"{case['id']} missing {field}")

    def test_difficulty_range(self):
        for case in self.cases:
            self.assertGreaterEqual(case["difficulty"], 1)
            self.assertLessEqual(case["difficulty"], 5)

    def test_unique_ids(self):
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_references_present(self):
        for case in self.cases:
            self.assertGreaterEqual(
                len(case["references"]), 1, f"{case['id']} has no references"
            )
            for ref in case["references"]:
                self.assertIn("title", ref)
                self.assertIn("url_or_doi", ref)

    def test_consistency(self):
        errors = validate_consistency(self.cases)
        self.assertEqual(errors, [])

    def test_id_format(self):
        import re

        for case in self.cases:
            self.assertRegex(case["id"], r"^[a-z][a-z-]*-\d{3}$")

    def test_version_format(self):
        import re

        for case in self.cases:
            self.assertRegex(case["version"], r"^\d+\.\d+$")


class TestSchema(unittest.TestCase):
    def test_schema_valid_json(self):
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        self.assertIn("$schema", schema)
        self.assertIn("properties", schema)


if __name__ == "__main__":
    unittest.main()
