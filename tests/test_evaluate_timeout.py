import importlib.util
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "evaluate.py"
SPEC = importlib.util.spec_from_file_location("evaluate", SCRIPT)
evaluate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluate)


class EvaluateTimeoutTest(unittest.TestCase):
    def test_wall_timeout_bounds_elapsed_time(self):
        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, "exceeded 1s"):
            with evaluate.wall_timeout(1):
                time.sleep(5)
        self.assertLess(time.monotonic() - started, 2)


if __name__ == "__main__":
    unittest.main()
