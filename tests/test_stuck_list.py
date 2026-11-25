"""Stuck files go to the user as one list; their answer is written back (plan 83, B-14)."""

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

FRESH = """# 017 — Parser — stuck gates

**Type:** stuck
**Status:** open
**Stuck gates:** `final-review`

## final-review

**Gate:** final review of loc/inbox/done/015-plan-parser.md
**Architect (Triage):** plan — the rounds went in circles on the time parser.
**Next:** <file>

### What remains
- `parse.py:41` — "around five" still parses as 05:00

## Resolution
<empty until resolved>
"""


def stuck_list(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "stuck_list.py"), *args,
                           "--project", str(cwd)], capture_output=True, text=True, encoding="utf-8", env=env)


def project(test: unittest.TestCase) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=SCRATCH))
    test.addCleanup(shutil.rmtree, path, True)
    (path / "loc" / "inbox" / "done").mkdir(parents=True)
    return path


class StuckListTest(unittest.TestCase):
    def setUp(self):
        self.cwd = project(self)
        inbox = self.cwd / "loc" / "inbox"
        (inbox / "017-stuck-parser.md").write_text(FRESH, encoding="utf-8")
        replanned = FRESH.replace("# 017", "# 021").replace("**Status:** open", "**Status:** open\n**Replanned:** 024")
        (inbox / "021-stuck-parser-again.md").write_text(replanned, encoding="utf-8")
        retried = FRESH.replace("# 017", "# 030").replace("plan — the rounds", "let go — the rounds") \
            + "\n## final-review (rounds 4–6)\n"
        (inbox / "030-stuck-labels.md").write_text(retried, encoding="utf-8")

    def test_one_list_with_the_ladder(self):
        result = stuck_list(self.cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        items = {item["number"]: item for item in data["items"]}
        self.assertEqual(sorted(items), ["017", "021", "030"])
        self.assertEqual(items["017"]["what"], '`parse.py:41` — "around five" still parses as 05:00')
        self.assertEqual((items["017"]["recommendation"], items["017"]["ladder"]), ("plan", "fresh"))
        self.assertEqual(items["021"]["ladder"], "replanned as plan 024")
        self.assertEqual((items["030"]["recommendation"], items["030"]["ladder"]), ("let go", "retry used"))
        self.assertIn('1. 017 — `parse.py:41` — "around five" still parses as 05:00 — architect: plan — fresh',
                      data["text"])

    def test_approve_and_let_go_write_the_answer(self):
        approved = stuck_list(self.cwd, "--approve", "021", "--words", "1 plan, the rest let go")
        self.assertEqual(approved.returncode, 0, approved.stderr)
        text = (self.cwd / "loc" / "inbox" / "021-stuck-parser-again.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"\*\*Status:\*\* open\n\*\*Approved by user:\*\* \d{4}-\d{2}-\d{2} — 1 plan, the rest")
        gone = stuck_list(self.cwd, "--let-go", "030", "--words", "the rest let go")
        self.assertEqual(gone.returncode, 0, gone.stderr)
        self.assertFalse((self.cwd / "loc" / "inbox" / "030-stuck-labels.md").exists())
        closed = (self.cwd / "loc" / "inbox" / "done" / "030-stuck-labels.md").read_text(encoding="utf-8")
        self.assertRegex(closed, r"\*\*Status:\*\* closed \d{4}-\d{2}-\d{2} — let go")
        self.assertRegex(closed, r"## Resolution\nLet go by the user \d{4}-\d{2}-\d{2}: the rest let go\n")
        self.assertNotIn("<empty until resolved>", closed)
        self.assertEqual(stuck_list(self.cwd, "--let-go", "999", "--words", "x").returncode, 1)
        self.assertEqual(stuck_list(self.cwd, "--approve", "017").returncode, 2)

    def test_director_shows_the_list_instead_of_planning_stuck_files(self):
        director = (ROOT / "skills" / "loc-director" / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("scripts/stuck_list.py", "--approve <NNN>", "--let-go <NNN>", "one line"):
            self.assertIn(marker, director)


if __name__ == "__main__":
    unittest.main()
