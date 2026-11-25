"""scripts/moves.py: the moves of past divergent milestones (plan 86, B-04)."""

import unittest

from tests.test_scripts import run, scratch_dir


class MovesTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)

    def test_add_appends_and_show_is_newest_first(self):
        first = run("moves.py", "add", "a name from the one verb", "--plan", "007", cwd=self.project)
        self.assertEqual(first.returncode, 0, first.stderr)
        run("moves.py", "add", "a tagline  written as a timetable", "--plan", "008", cwd=self.project)
        text = (self.project / "loc" / "moves.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Moves"))
        self.assertIn("last 12", text)  # the header comes from templates/loc/moves.md
        self.assertRegex(text, r"- \d{4}-\d\d-\d\d \(plan 007\): a name from the one verb\n")
        shown = run("moves.py", "show", cwd=self.project).stdout.splitlines()
        self.assertEqual(len(shown), 2)
        self.assertTrue(shown[0].endswith("(plan 008): a tagline written as a timetable"))
        last = run("moves.py", "show", "--last", "1", cwd=self.project).stdout.splitlines()
        self.assertEqual(last, shown[:1])

    def test_show_without_a_file_prints_nothing(self):
        result = run("moves.py", "show", cwd=self.project)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_remove_drops_the_last_entry_with_that_move(self):
        run("moves.py", "add", "a name from the one verb", "--plan", "007", cwd=self.project)
        run("moves.py", "add", "type | image split", "--plan", "008", cwd=self.project)
        self.assertEqual(run("moves.py", "remove", "Type  |  Image split", cwd=self.project).returncode, 0)
        shown = run("moves.py", "show", cwd=self.project).stdout.splitlines()
        self.assertEqual(len(shown), 1)
        self.assertTrue(shown[0].endswith("a name from the one verb"))
        self.assertEqual(run("moves.py", "remove", "never added", cwd=self.project).returncode, 1)

    def test_an_empty_move_is_refused(self):
        self.assertEqual(run("moves.py", "add", "  ", cwd=self.project).returncode, 1)
