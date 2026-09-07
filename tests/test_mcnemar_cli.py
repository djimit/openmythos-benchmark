import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestMcNemarCli(unittest.TestCase):
    def test_category_regression_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = root / "before.jsonl"
            after = root / "after.jsonl"
            output = root / "result.json"
            before.write_text(json.dumps({"case_id": "a", "category": "canary", "avg_score": 5}) + "\n")
            after.write_text(json.dumps({"case_id": "a", "category": "canary", "avg_score": 1}) + "\n")
            result = subprocess.run(
                ["python3", "scripts/mcnemar_test.py", "--before", str(before), "--after", str(after), "--output", str(output)],
                cwd=Path(__file__).parent.parent,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(output.read_text())["category_regressions"], ["canary"])


if __name__ == "__main__":
    unittest.main()
