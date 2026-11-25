"""scripts/seed.py: a random start for a divergent milestone (plan 86, B-04)."""

import json
import unittest

from tests.test_scripts import run, scratch_dir


class SeedTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)

    def seed(self, *args):
        result = run("seed.py", *args, cwd=self.project)
        return result.returncode, json.loads(result.stdout)

    def test_every_kind_draws_its_axes(self):
        for kind, axes in (("visual", {"method", "colours", "layout", "typography", "verb", "scale"}),
                           ("text", {"voice", "entry", "register"}),
                           ("idea", {"verb", "constraint", "scale", "emphasis"})):
            code, out = self.seed(kind)
            self.assertEqual(code, 0)
            self.assertEqual(out["kind"], kind)
            self.assertEqual(set(out["seed"]), axes)
        history = (self.project / "loc" / "seeds.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(history), 3)

    def test_keep_holds_an_axis(self):
        code, out = self.seed("text", "--keep", "voice=a court record")
        self.assertEqual(code, 0)
        self.assertEqual(out["seed"]["voice"], "a court record")

    def test_keep_holds_an_axis_outside_only(self):
        code, out = self.seed("visual", "--only", "method", "--keep", "colours=two inks only")
        self.assertEqual(code, 0)
        self.assertEqual(out["seed"]["colours"], "two inks only")
        self.assertEqual(set(out["seed"]), {"method", "colours"})

    def test_values_of_the_last_12_seeds_are_skipped(self):
        verbs = [self.seed("idea", "--only", "verb")[1]["seed"]["verb"] for _ in range(13)]
        self.assertEqual(len(set(verbs)), 13, verbs)

    def test_an_exhausted_axis_still_draws(self):
        for _ in range(20):
            code, out = self.seed("text", "--only", "register")
            self.assertEqual(code, 0)
            self.assertEqual(list(out["seed"]), ["register"])

    def test_an_unknown_axis_is_a_problem(self):
        code, out = self.seed("text", "--only", "colours")
        self.assertEqual(code, 1)
        self.assertIn("not an axis of text", out["issues"][0])
