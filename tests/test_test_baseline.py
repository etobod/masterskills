"""Tests for scripts/test_baseline.py: the copy of a project's tests at the start of a plan."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch projects stay inside the repository (CLAUDE.md rule 1), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"

TEST_PLAN = """# Test plan

## (a) Warstwy i komendy
| unit | `python -m unittest` | gate | fast |

## (e) What a test looks like here
<!-- przykład: `ignored_dir/` -->
- `unittest`, testy w `tests/` oraz `test_*.py` w katalogu głównym.
"""


def run(project: Path, *args: str) -> tuple:
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "test_baseline.py"), "--plan", "007", *args],
                            cwd=project, capture_output=True, text=True, encoding="utf-8")
    return result.returncode, json.loads(result.stdout)


class TestBaselineTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        # No `git init`: the script must work outside git.
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)

    def write(self, rel: str, text: str) -> None:
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def make_project(self) -> None:
        self.write("loc/TEST-PLAN.md", TEST_PLAN)
        self.write("tests/test_a.py", "a = 1\n")
        self.write("test_root.py", "b = 1\n")
        self.write("ignored_dir/test_x.py", "x\n")
        self.write("app.py", "c = 1\n")

    def test_copies_tests_named_in_section_e_outside_git(self):
        self.make_project()
        code, out = run(self.project)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["files"], ["loc/TEST-PLAN.md", "test_root.py", "tests/test_a.py"])
        manifest = self.project / "loc" / "state" / "007" / "baseline" / "manifest.json"
        self.assertEqual(set(json.loads(manifest.read_text(encoding="utf-8"))["files"]), set(out["files"]))

    def test_compare_lists_changed_added_and_removed(self):
        self.make_project()
        run(self.project)
        self.write("tests/test_a.py", "a = 2\n")
        self.write("tests/test_new.py", "n\n")
        (self.project / "test_root.py").unlink()
        code, out = run(self.project, "--compare")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["changed"], ["tests/test_a.py"])
        self.assertEqual(out["added"], ["tests/test_new.py"])
        self.assertEqual(out["removed"], ["test_root.py"])

    def test_existing_copy_is_kept(self):
        self.make_project()
        run(self.project)
        self.write("tests/test_a.py", "a = 2\n")
        code, out = run(self.project)
        self.assertEqual((code, out["created"]), (0, False))
        self.assertEqual(run(self.project, "--compare")[1]["changed"], ["tests/test_a.py"])

    def test_without_test_plan_exits_0(self):
        code, out = run(self.project)
        self.assertEqual(code, 0)
        self.assertIn("nothing to copy", out["message"])
        self.assertFalse((self.project / "loc" / "state").exists())


if __name__ == "__main__":
    unittest.main()
