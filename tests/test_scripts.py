"""Tests for the scripts that create and read the project's `loc/` files."""

import json
import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch projects stay inside the repository (CLAUDE.md rule 1), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def scratch_dir(test: unittest.TestCase) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=SCRATCH))
    test.addCleanup(shutil.rmtree, path, True)
    return path


def run(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8")


class InitProjectTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)

    def test_creates_loc_and_one_ignore_line_idempotently(self):
        first = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)
        second = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)
        for rel in ("loc/inbox/done", "loc/PRD.md", "loc/PATTERNS.md", "loc/MEMORY.md"):
            self.assertTrue((self.project / rel).exists(), rel)
        self.assertFalse((self.project / "inbox").exists())
        self.assertFalse((self.project / "docs").exists())
        lines = (self.project / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count("loc/"), 1)
        self.assertIn(".gitignore", first["created"])
        self.assertEqual(second["created"] + second["updated"], [])

    def test_test_plan_comes_only_from_a_plan(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        self.assertFalse((self.project / "loc" / "TEST-PLAN.md").exists())
        self.assertIn("## Project-specific workflow", (self.project / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_git_sees_nothing_from_loc(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        status = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=self.project,
                                capture_output=True, text=True, check=True).stdout
        self.assertNotIn("loc/", status)


class NextNumberTest(unittest.TestCase):
    def test_numbers_across_inbox_and_done_and_creates_the_file(self):
        project = scratch_dir(self)
        (project / "loc" / "inbox" / "done").mkdir(parents=True)
        (project / "loc" / "inbox" / "done" / "004-plan-a.md").write_text("x", encoding="utf-8")
        out = run("next_number.py", "--project", ".", "--type", "odlozone", "--slug", "later", "--title", "Later",
                  "--source", "test", cwd=project)
        result = json.loads(out.stdout)
        self.assertEqual(result["number"], "005")
        self.assertEqual(result["path"], "loc/inbox/005-odlozone-later.md")
        self.assertTrue((project / result["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
