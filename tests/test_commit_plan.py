"""Tests for scripts/commit_plan.py: one commit of the plan's files at the end of a plan."""

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


class CommitPlanTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "core.autocrlf", "false")
        (self.project / ".gitignore").write_text("loc/\n", encoding="utf-8")

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.project, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def write(self, rel: str, text: str) -> None:
        (self.project / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.project / rel).write_text(text, encoding="utf-8")

    def start_plan(self) -> Path:
        """Take the plan's first snapshot and write the state file."""
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "snapshot.py"), "--project", str(self.project)],
                             capture_output=True, text=True, encoding="utf-8")
        state = self.project / "loc" / "state" / "001.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"milestones": [{"id": "M1", "start": json.loads(out.stdout)["hash"]}]}),
                         encoding="utf-8")
        return state

    def commit(self, *args: str) -> tuple:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "commit_plan.py"),
                                 "--project", str(self.project), "--state", "loc/state/001.json", *args],
                                capture_output=True, text=True, encoding="utf-8")
        return result.returncode, json.loads(result.stdout)

    def state(self) -> dict:
        return json.loads((self.project / "loc" / "state" / "001.json").read_text(encoding="utf-8"))

    def test_commits_only_the_plans_files(self):
        self.write("app.py", "x = 1\n")
        self.write("notes.txt", "a\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "chore: start")
        self.write("notes.txt", "a\nthe user's own edit\n")
        self.start_plan()
        self.write("app.py", "x = 2\n")
        self.write("new.py", "y = 1\n")
        self.write("loc/inbox/001-plan-x.md", "# plan\n")
        code, out = self.commit("--message", "feat(app): change x")
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(out["files"]), ["app.py", "new.py"])
        self.assertEqual(self.git("show", "--name-only", "--format=", "HEAD").splitlines(), ["app.py", "new.py"])
        self.assertEqual(self.git("status", "--porcelain"), "M notes.txt")
        self.assertEqual(self.state()["commit"], self.git("rev-parse", "HEAD"))

    def test_first_commit_in_an_empty_repository(self):
        self.start_plan()
        self.write("page.html", "<p>hi</p>\n")
        code, out = self.commit("--message", "feat: add the page")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.git("log", "--format=%s"), "feat: add the page")
        self.assertIn("page.html", self.git("show", "--name-only", "--format=", "HEAD"))

    def test_rejects_a_bad_message(self):
        self.start_plan()
        self.write("page.html", "<p>hi</p>\n")
        for message in ("added the page", "feat: add the page\n\nCo-authored-by: Claude <x@y>",
                        "feat: add the page written by Claude", "fix: AI generated fix"):
            with self.subTest(message=message):
                code, out = self.commit("--message", message)
                self.assertEqual(code, 1, out)
        result = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"], cwd=self.project, capture_output=True)
        self.assertNotEqual(result.returncode, 0, "nothing may be committed")
        self.assertNotIn("commit", self.state())

    def test_nothing_to_commit_and_skip(self):
        self.start_plan()
        self.write("loc/MEMORY.md", "# Dziennik\n")
        code, out = self.commit("--message", "docs: plan notes")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.state()["commit"], "none")
        code, out = self.commit("--skip", "CLAUDE.md: the user commits")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.state()["commit"], "skipped: CLAUDE.md: the user commits")


if __name__ == "__main__":
    unittest.main()
