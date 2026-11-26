"""suite_size.py says when the test suite has grown enough for a whole-suite review."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scripts import run, scratch_dir  # noqa: E402


class SuiteSizeTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)

    def write(self, rel: str, count: int) -> None:
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n" * count, encoding="utf-8")

    def size(self, *extra) -> dict:
        out = run("suite_size.py", "--project", ".", *extra, cwd=self.project)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return json.loads(out.stdout)

    def test_tests_over_twice_the_code_are_due_without_a_review(self):
        # A suite three times the code grew only by additions: nobody ever removed a test.
        self.write("app.js", 100)
        self.write("web/drill.test.js", 150)
        self.write("tests/test_tree.py", 100)
        self.write("loc/inbox/001-plan.md", 5000)   # loc/ is not the project
        self.write("data/huge.json", 5000)          # data is not code
        self.write("tests/fixtures/recording.json", 5000)  # nor are fixtures tests
        result = self.size()
        self.assertEqual((result["tests"], result["code"]), (250, 100))
        self.assertTrue(result["due"])
        self.write("app.js", 200)
        self.assertFalse(self.size()["due"])

    def test_a_review_resets_the_count_and_growth_by_half_is_due_again(self):
        self.write("app.py", 10)
        self.write("tests/test_app.py", 100)
        self.assertTrue(self.size("--record", "007")["due"])
        self.assertFalse(self.size("--reviewed")["due"])
        self.write("tests/test_more.py", 40)
        self.assertFalse(self.size()["due"])
        self.write("tests/test_more.py", 50)
        result = self.size("--record", "008")
        self.assertTrue(result["due"])
        self.assertIsNotNone(result["reviewed_at"])
        history = (self.project / "loc" / "state" / "qa-history.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual([line.split()[1:3] for line in history],
                         [["007", "suite-size"], ["-", "suite-review"], ["008", "suite-size"]])

    def test_given_test_paths_replace_the_search(self):
        self.write("app.py", 100)
        self.write("checks/a.py", 300)
        self.write("tests/test_app.py", 50)
        result = self.size("--tests", "checks/")
        self.assertEqual((result["tests"], result["code"]), (300, 150))
        self.assertEqual(self.size("--tests", "./checks")["tests"], 300)
        self.assertEqual(self.size("--tests", "checks/*.py", "tests")["tests"], 350)
        # A path that matches nothing is an error, not a suite of zero lines.
        out = run("suite_size.py", "--project", ".", "--tests", "spec/", cwd=self.project)
        self.assertEqual(out.returncode, 2)
        self.assertIn("spec", out.stdout)


if __name__ == "__main__":
    unittest.main()
