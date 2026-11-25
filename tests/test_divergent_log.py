"""scripts/divergent_log.py: the log of a divergent milestone and its proof (plan 86, B-01)."""

import unittest

from tests.test_scripts import run, scratch_dir


class DivergentLogTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        (self.project / "loc").mkdir()
        self.log = "loc/state/007/divergent-M1.md"

    def log_cmd(self, *args):
        return run("divergent_log.py", *args, "--log", self.log, cwd=self.project)

    def moves(self, text: str):
        (self.project / "loc" / "moves.md").write_text("# Moves\n\n" + text, encoding="utf-8")

    def full(self, safe=("B",), pick_by="user", verdict="pass", built=True, move_saved=True):
        self.assertEqual(self.log_cmd("--start", "--default", "a made-up word, \"Your X, simplified\"").returncode, 0)
        variants = {"A": ("name from the one verb the tool does", "the PRD says it only counts"),
                    "B": ("a plain descriptive name", "safe: says what it is"),
                    "C": ("a name taken from the terminal prompt", "CLAUDE.md: it lives in a terminal")}
        for name, (move, reason) in variants.items():
            extra = ["--safe"] if name in safe else []
            result = self.log_cmd("--variant", "--name", name, "--move", move, "--reason", reason, *extra)
            self.assertEqual(result.returncode, 0, result.stderr)
        for name in variants:
            self.log_cmd("--verdict", "--name", name, "--result", verdict if name == "A" else "pass",
                         "--why", "fits only this tool")
        self.log_cmd("--pick", "--name", "A", "--by", "interim")
        if pick_by == "user":
            self.log_cmd("--pick", "--name", "A", "--by", "user")
        if built:
            self.assertEqual(self.log_cmd("--built", "--working", "pass").returncode, 0)
        if move_saved:
            self.moves("- 2026-11-25 (plan 007): Name From The One Verb The Tool Does\n")

    def check(self):
        result = self.log_cmd("--check")
        return result.returncode, result.stdout.strip()

    def test_a_full_log_is_ok(self):
        self.full()
        self.assertEqual(self.check(), (0, "ok"))

    def test_a_variant_needs_a_reason(self):
        self.log_cmd("--start", "--default", "x")
        result = self.log_cmd("--variant", "--name", "A", "--move", "m", "--reason", " ")
        self.assertEqual(result.returncode, 1)
        self.assertIn("reason", result.stdout)

    def test_two_safe_variants_fail(self):
        self.full(safe=("A", "B"))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("at most one safe variant", out)

    def test_the_pick_needs_a_pass(self):
        self.full(verdict="fail")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("A has no critic's pass", out)

    def test_an_interim_pick_waits_for_the_user(self):
        self.full(pick_by="interim")
        self.assertEqual(self.check(), (1, "waiting: user pick"))

    def test_the_move_must_be_in_moves_md(self):
        self.full(move_saved=False)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("loc/moves.md", out)
        self.assertIn("moves.py add", out)

    def test_fewer_than_two_variants_and_no_build_fail(self):
        self.log_cmd("--start", "--default", "x")
        self.log_cmd("--variant", "--name", "A", "--move", "m", "--reason", "r")
        code, out = self.check()
        self.assertEqual(code, 1)
        for missing in ("2 to 4 variants", "with the critic's pass, found 0", "no pick"):
            self.assertIn(missing, out)

    def test_a_reworked_variant_replaces_the_first(self):
        self.full(verdict="fail")
        self.log_cmd("--variant", "--name", "A", "--move", "name from the one verb the tool does",
                     "--reason", "reworked once")
        self.log_cmd("--verdict", "--name", "A", "--result", "pass", "--why", "now fits")
        self.assertEqual(self.check(), (0, "ok"))

    def test_failed_variants_do_not_count(self):
        self.full()
        for name in ("B", "C"):
            self.log_cmd("--verdict", "--name", name, "--result", "fail", "--why", "the default again")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("at least 2 variants with the critic's pass, found 1", out)

    def test_a_reworked_variant_loses_its_verdict(self):
        self.full()
        self.log_cmd("--variant", "--name", "A", "--move", "name from the one verb the tool does", "--reason", "redone")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("A has no critic's pass", out)

    def test_at_most_four_variants(self):
        self.full()
        for name in ("D", "E"):
            self.log_cmd("--variant", "--name", name, "--move", "m " + name, "--reason", "a fact")
        self.assertIn("2 to 4 variants, found 5", self.check()[1])

    def test_a_move_only_in_the_header_or_inside_another_is_not_recorded(self):
        self.full(move_saved=False)
        self.moves("A move such as a name from the one verb the tool does.\n\n"
                   "- 2026-11-25 (plan 006): a name from the one verb the tool does, read backwards\n")
        self.assertIn("the move of A is not in", self.check()[1])

    def test_a_move_with_a_bar_matches_what_moves_py_added(self):
        self.full(move_saved=False)
        self.log_cmd("--variant", "--name", "A", "--move", "type | image split", "--reason", "the PRD")
        self.log_cmd("--verdict", "--name", "A", "--result", "pass", "--why", "fits")
        self.assertEqual(run("moves.py", "add", "type | image split", cwd=self.project).returncode, 0)
        self.assertEqual(self.check(), (0, "ok"))

    def test_another_pick_after_the_interim_build_needs_its_own_build(self):
        self.full(pick_by="interim")
        self.log_cmd("--pick", "--name", "C", "--by", "user")
        run("moves.py", "add", "a name taken from the terminal prompt", cwd=self.project)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("C is not built", out)
        self.log_cmd("--built", "--working", "pass")
        self.assertEqual(self.check(), (0, "ok"))

    def test_the_user_picking_the_built_variant_is_ok(self):
        self.full(pick_by="interim")
        self.log_cmd("--pick", "--name", "A", "--by", "user")
        self.assertEqual(self.check(), (0, "ok"))

    def test_failing_working_parts_are_not_ok(self):
        self.full(built=False)
        self.log_cmd("--built", "--working", "fail")
        self.assertIn("the working parts of A fail", self.check()[1])

    def test_built_needs_a_pick_and_the_working_parts(self):
        self.log_cmd("--start", "--default", "x")
        self.assertEqual(self.log_cmd("--built", "--working", "pass").returncode, 1)
        self.full()
        self.assertEqual(self.log_cmd("--built").returncode, 1)

    def test_none_of_them_is_recorded(self):
        self.full(pick_by="interim")
        self.log_cmd("--pick", "--name", "none", "--by", "user")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("the user picked none", out)
        self.assertNotIn("is not built", out)

    def test_no_log_fails(self):
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("no log", out)
