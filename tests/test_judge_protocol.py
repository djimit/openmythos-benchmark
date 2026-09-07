import unittest

from scripts import judge, reliability_gate


class JudgeProtocolTest(unittest.TestCase):
    def test_score_must_be_a_single_digit(self):
        self.assertEqual(judge.parse_score(" 4\n"), "4")
        self.assertEqual(judge.parse_score("4|Minor issue"), "4")
        self.assertEqual(judge.parse_score("4 | Minor issue"), "4")
        for malformed in ("Score: 5", "4 because correct", "", "6"):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    judge.parse_score(malformed)

    def test_judged_entry_records_rubric_version(self):
        entry = judge.judged_entry({"case_id": "demo"}, 4, "judge")
        self.assertEqual(entry["judge_rubric_version"], "2.0-default")
        self.assertEqual(len(set(judge.JUDGE_RUBRIC_VERSIONS.values())), 3)

    def test_reliability_rejects_mixed_rubrics(self):
        traces = {
            "a": {"x": {"judge_rubric_version": "1"}},
            "b": {"x": {"judge_rubric_version": "2"}},
        }
        with self.assertRaises(SystemExit):
            reliability_gate.require_one_rubric(traces)


if __name__ == "__main__":
    unittest.main()
