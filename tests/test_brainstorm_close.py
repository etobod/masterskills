"""Tests for scripts/brainstorm_close.py: a brainstorm closes when everything in it is planned."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"

BRAINSTORM = """# 004 — Greeting language

**Type:** brainstorm
**Status:** approved 2026-11-20
**Created:** 2026-11-19 10:00
**Source:** conversation
**Created by:** loc-brainstorm

## Topic
Greet visitors in their language.

## Notes
- The browser sends Accept-Language.

## Decisions
- B-01 — Read Accept-Language. Reason: no login.
- ~~B-02 — Ask the visitor.~~ → replaced by B-03
- B-03 — Fall back to English.
- B-04 — The project is a greeting page. → moved to loc/PRD.md Goal

## Open
{open}

## Resolution
<empty until handled: which plan came from this>
"""


class BrainstormCloseTest(unittest.TestCase):
    def project(self, open_items: str = "<what is not decided yet>") -> Path:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        (project / "loc" / "inbox" / "done").mkdir(parents=True)
        (project / "loc" / "inbox" / "004-brainstorm-greeting.md").write_text(
            BRAINSTORM.format(open=open_items), encoding="utf-8")
        return project

    def run_close(self, project: Path, plan: str, covers: str) -> tuple:
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "brainstorm_close.py"), "--project",
                                 str(project), "--brainstorm", "004", "--plan", plan, "--covers", covers],
                                capture_output=True, text=True, encoding="utf-8", env=env)
        return result.returncode, json.loads(result.stdout)

    def test_partial_cover_leaves_it_open(self):
        project = self.project()
        code, out = self.run_close(project, "087", "B-01")
        self.assertEqual((code, out["closed"], out["unplanned"]), (0, False, ["B-03"]))
        text = (project / "loc" / "inbox" / "004-brainstorm-greeting.md").read_text(encoding="utf-8")
        self.assertIn("- B-01 — Read Accept-Language. Reason: no login. → plan 087", text)
        self.assertIn("**Status:** approved", text)

    def test_full_cover_closes_and_moves(self):
        project = self.project()
        self.run_close(project, "087", "B-01")
        code, out = self.run_close(project, "088", "B-03")
        self.assertEqual((code, out["closed"]), (0, True))
        self.assertFalse((project / "loc" / "inbox" / "004-brainstorm-greeting.md").exists())
        text = (project / "loc" / "inbox" / "done" / "004-brainstorm-greeting.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** closed — planned in plan 087, plan 088", text)
        self.assertIn("Planned in plan 087, plan 088.", text)
        self.assertNotIn("<empty until handled", text)

    def test_struck_decisions_do_not_count_and_cannot_be_covered(self):
        project = self.project()
        code, out = self.run_close(project, "087", "B-01,B-03")
        self.assertTrue(out["closed"])
        project = self.project()
        code, out = self.run_close(project, "087", "B-02")
        self.assertEqual(code, 2)
        self.assertIn("B-02", out["error"])

    def test_unknown_decision_is_an_error_and_writes_nothing(self):
        project = self.project()
        before = (project / "loc" / "inbox" / "004-brainstorm-greeting.md").read_text(encoding="utf-8")
        code, out = self.run_close(project, "087", "B-01,B-09")
        self.assertEqual(code, 2)
        self.assertIn("B-09", out["error"])
        self.assertEqual(before, (project / "loc" / "inbox" / "004-brainstorm-greeting.md").read_text(encoding="utf-8"))

    def test_open_items_keep_it_open(self):
        project = self.project("- Which languages first? Recommended: the five most visited.")
        code, out = self.run_close(project, "087", "B-01,B-03")
        self.assertEqual((out["closed"], out["open_items"], out["unplanned"]), (False, True, []))


if __name__ == "__main__":
    unittest.main()
