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

    def test_reports_the_empty_sections_a_brainstorm_may_fill(self):
        fresh = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)["empty"]
        self.assertEqual(fresh["loc/PRD.md"], ["Goal", "Core idea", "Scenarios"])
        self.assertIn("Commands", fresh["CLAUDE.md"])
        self.assertIn("Limits", fresh["CLAUDE.md"])
        claude = self.project / "CLAUDE.md"
        text = claude.read_text(encoding="utf-8").replace("## Limits\n", "## Limits\nNo cloud services.\n")
        claude.write_text(text, encoding="utf-8")
        prd = self.project / "loc" / "PRD.md"
        prd.write_text(prd.read_text(encoding="utf-8").replace(
            "## Goal\n", "## Goal\nA diary that stays offline.\n"), encoding="utf-8")
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        again = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)["empty"]
        self.assertNotIn("Limits", again["CLAUDE.md"])
        self.assertIn("Commands", again["CLAUDE.md"])
        self.assertEqual(again["loc/PRD.md"], ["Core idea", "Scenarios"])
        after = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)

    def test_check_reports_without_writing(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        claude = self.project / "CLAUDE.md"
        text = claude.read_text(encoding="utf-8").replace("## Limits\n", "## Limits\nJeden plik, zero zależności.\n")
        text = text.replace("## Invariants\n", "## Invariants\n- One file only.\n")
        claude.write_text(text, encoding="utf-8")
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        out = run("init_project.py", "--project", ".", "--check", cwd=self.project)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertIn("Goal", result["empty"]["loc/PRD.md"])
        self.assertEqual(result["not_english"], ["Limits"])
        self.assertNotIn("created", result)
        after = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)

    def test_check_reports_a_missing_prd_section(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        prd = self.project / "loc" / "PRD.md"
        prd.write_text("# PRD\n\n## Goal\nA diary.\n\n## Core idea\n- Offline.\n\n## Directions\n", encoding="utf-8")
        before = prd.read_bytes()
        result = json.loads(run("init_project.py", "--project", ".", "--check", cwd=self.project).stdout)
        self.assertEqual(result["empty"]["loc/PRD.md"], ["Scenarios"])
        self.assertEqual(prd.read_bytes(), before)

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
        out = run("next_number.py", "--project", ".", "--type", "deferred", "--slug", "later", "--title", "Later",
                  "--source", "test", cwd=project)
        result = json.loads(out.stdout)
        self.assertEqual(result["number"], "005")
        self.assertEqual(result["path"], "loc/inbox/005-deferred-later.md")
        self.assertTrue((project / result["path"]).is_file())


class ReviewDiffTest(unittest.TestCase):
    def test_review_without_commits(self):
        project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        (project / "app.js").write_text("const x = 1;\n", encoding="utf-8")
        (project / "loc").mkdir()
        (project / "loc" / "notes.md").write_text("x\n", encoding="utf-8")
        out = run("review_diff.py", "--project", ".", "--from", "HEAD", "--out", "loc/review/x.diff", cwd=project)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual(result["files"], ["app.js"])
        self.assertIn("+const x = 1;", (project / "loc" / "review" / "x.diff").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
