"""Tests for scripts/frame.py: no goal, no work."""
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
TEMPLATE = (ROOT / "templates" / "loc" / "PRD.md").read_text(encoding="utf-8")
FULL = ("# PRD\n\n## Goal\nA guide that tells a player which items to keep.\n\n"
        "## Core idea\n- **Data first.** Prices come from the trade site, never typed in.\n\n"
        "## Scenarios\n1. A player pastes an item and sees its worth within a second.\n")
COMMANDS = "# CLAUDE.md\n\n## Commands\n- Tests: `python -m unittest`\n"


class FrameTest(unittest.TestCase):
    def run_frame(self, prd: str = None, claude: str = COMMANDS) -> tuple:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        if prd is not None:
            (project / "loc").mkdir()
            (project / "loc" / "PRD.md").write_text(prd, encoding="utf-8")
        if claude is not None:
            (project / "CLAUDE.md").write_text(claude, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "frame.py"), "--project", str(project)],
                                capture_output=True, text=True, encoding="utf-8", env=env)
        return result.returncode, json.loads(result.stdout)

    def test_full_frame_passes(self):
        self.assertEqual(self.run_frame(FULL), (0, {"ok": True, "missing": []}))

    def test_empty_template_misses_all_three(self):
        code, out = self.run_frame(TEMPLATE.replace("{PROJECT}", "poe"))
        self.assertEqual(code, 1)
        self.assertEqual(out["missing"], ["loc/PRD.md ## Goal", "loc/PRD.md ## Core idea", "loc/PRD.md ## Scenarios"])

    def test_decisions_alone_are_no_frame(self):
        # The analysed project: an empty template with a filled Decisions list.
        prd = TEMPLATE.replace("{PROJECT}", "poe") + "\n- D-01: prices in chaos orbs. Reason: x. (2026-11-01)\n"
        code, out = self.run_frame(prd)
        self.assertEqual(code, 1)
        self.assertIn("loc/PRD.md ## Goal", out["missing"])

    def test_missing_heading_and_missing_file(self):
        code, out = self.run_frame(FULL.split("## Scenarios")[0])
        self.assertEqual(out["missing"], ["loc/PRD.md ## Scenarios"])
        code, out = self.run_frame(None)
        self.assertEqual(code, 1)
        self.assertEqual(len([m for m in out["missing"] if m.startswith("loc/PRD.md")]), 3)

    def test_test_command_is_part_of_the_frame(self):
        for claude in (None, "# CLAUDE.md\n\n## Commands\n- Run: `npm start`\n",
                       "# CLAUDE.md\n\n## Commands\n<!-- Tests: `npm test` -->\n"):
            with self.subTest(claude=claude):
                code, out = self.run_frame(FULL, claude)
                self.assertEqual((code, out["missing"]), (1, ["CLAUDE.md ## Commands: test command"]))


if __name__ == "__main__":
    unittest.main()
