"""A course takes a stuck file only with the user's approval, or as the first plan of a Triage `plan` (B-14)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_director import course, project, section  # noqa: E402
from test_stuck_list import FRESH  # noqa: E402


class CourseStuckTest(unittest.TestCase):
    def setUp(self):
        self.cwd = project(self)
        self.inbox = self.cwd / "loc" / "inbox"
        (self.inbox / "017-stuck-parser.md").write_text(FRESH, encoding="utf-8")
        again = FRESH.replace("# 017", "# 021").replace("**Status:** open", "**Status:** open\n**Replanned:** 024")
        (self.inbox / "021-stuck-parser-again.md").write_text(again, encoding="utf-8")

    def test_a_replanned_stuck_file_needs_approval(self):
        refused = course(self.cwd, "start", "--limit", "goal", "--agreed", "x",
                         "--item", "loc/inbox/021-stuck-parser-again.md")
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("not approved by the user", refused.stdout)
        self.assertNotIn("## Course", (self.cwd / "loc" / "PRD.md").read_text(encoding="utf-8"))
        path = self.inbox / "021-stuck-parser-again.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "**Status:** open", "**Status:** open\n**Approved by user:** 2026-11-25 — plan it"), encoding="utf-8")
        started = course(self.cwd, "start", "--limit", "goal", "--agreed", "x",
                         "--item", "loc/inbox/021-stuck-parser-again.md")
        self.assertEqual(started.returncode, 0, started.stdout)

    def test_the_first_plan_from_triage_goes_without_asking(self):
        started = course(self.cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "plan 084")
        self.assertEqual(started.returncode, 0, started.stdout)
        added = course(self.cwd, "add", "--item", "loc/inbox/017-stuck-parser.md", "--source", "plan 084")
        self.assertEqual(added.returncode, 0, added.stdout)
        refused = course(self.cwd, "add", "--item", "loc/inbox/021-stuck-parser-again.md", "--source", "plan 084")
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertNotIn("021-stuck", section(self.cwd))

    def test_a_let_go_verdict_is_not_planned_without_the_user(self):
        path = self.inbox / "017-stuck-parser.md"
        path.write_text(FRESH.replace("plan — the rounds", "let go — the rounds"), encoding="utf-8")
        refused = course(self.cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "loc/inbox/017-stuck-parser.md")
        self.assertEqual(refused.returncode, 1, refused.stdout)


if __name__ == "__main__":
    unittest.main()
