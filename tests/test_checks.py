"""The manual checks sheet: one HTML file in the inbox, points rated by number."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")


class ChecksSheetTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)
        (self.project / "loc" / "inbox" / "done").mkdir(parents=True)
        (self.project / "loc" / "inbox" / "done" / "006-plan-x.md").write_text("# 006 — x\n", encoding="utf-8")
        (self.project / "shot.png").write_bytes(PNG)

    def run_checks(self, *args, ok=True):
        out = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "checks.py"), "--project", str(self.project), *args],
                             capture_output=True, text=True, encoding="utf-8")
        if ok:
            self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
            return json.loads(out.stdout)
        self.assertNotEqual(out.returncode, 0)
        return out

    def add(self, title, *extra):
        return self.run_checks("--add", "--plan", "018", "--milestone", "M2", "--title", title,
                               "--look", "the sun beam hits the day side", *extra)

    def test_first_point_starts_a_sheet_with_the_next_inbox_number(self):
        result = self.add("Sun beam", "--step", "Open index.html", "--step", "Click Start | shot.png | 40,62",
                          "--image", "shot.png | 375 px", "--reference", "shot.png | reference",
                          "--expected", "a warm beam", "--seen", "the beam is cut")
        self.assertEqual(result["sheet"], "loc/inbox/007-U-checks.html")
        self.assertEqual(result["point"], 1)
        text = (self.project / result["sheet"]).read_text(encoding="utf-8")
        for part in ('data-point="1"', "Sun beam", "Click Start", 'left:40%;top:62%', "a warm beam",
                     "the beam is cut", "<b>1</b> open", "3 ok, 5 fix", "<title>007 — Manual checks</title>"):
            self.assertIn(part, text)
        images = sorted(p.name for p in (self.project / "loc" / "tmp" / "checks").iterdir())
        self.assertEqual(images, ["007-1-1.png", "007-1-2.png", "007-1-3.png"])
        self.assertIn("../tmp/checks/007-1-1.png", text)

    def test_points_are_appended_and_numbers_never_reused(self):
        self.add("One")
        self.assertEqual(self.add("Two")["point"], 2)
        self.run_checks("--rate", "--ok", "2")
        third = self.add("Three", "--again", "1")
        self.assertEqual(third["point"], 3)
        self.assertEqual(third["sheet"], "loc/inbox/007-U-checks.html")
        text = (self.project / third["sheet"]).read_text(encoding="utf-8")
        self.assertIn("again: 1", text)
        self.assertEqual([p["point"] for p in self.run_checks("--list")["points"]], [1, 3])

    def test_rating_moves_points_with_the_answer_and_deletes_their_images(self):
        self.add("One", "--image", "shot.png | 375 px")
        self.add("Two", "--blocking")
        self.add("Three")
        result = self.run_checks("--rate", "--ok", "1", "--fix", "3", "the shadow is too strong")
        self.assertEqual(result["moved"], [1, 3])
        self.assertEqual(result["fixes"], [{"point": 3, "plan": "018", "milestone": "M2", "title": "Three",
                                            "fix": "the shadow is too strong"}])
        self.assertEqual(result["open"], 1)
        self.assertFalse(result["closed"])
        open_text = (self.project / "loc/inbox/007-U-checks.html").read_text(encoding="utf-8")
        self.assertNotIn('data-point="1"', open_text)
        self.assertIn('data-point="2"', open_text)
        self.assertIn("<b>1</b> open", open_text)
        done = (self.project / "loc/inbox/done/007-U-checks.html").read_text(encoding="utf-8")
        self.assertIn('data-point="1"', done)
        self.assertIn("fix: the shadow is too strong", done)
        self.assertIn("screenshot removed after rating: 375 px", done)
        self.assertFalse((self.project / "loc/tmp/checks/007-1-1.png").exists())
        self.assertEqual(self.run_checks("--list")["points"][0]["blocking"], True)

    def test_last_point_closes_the_sheet_and_the_next_starts_a_new_one(self):
        self.add("One")
        result = self.run_checks("--rate", "--ok", "1")
        self.assertTrue(result["closed"])
        self.assertFalse((self.project / "loc/inbox/007-U-checks.html").exists())
        self.assertTrue((self.project / "loc/inbox/done/007-U-checks.html").exists())
        again = self.add("Two")
        self.assertEqual(again["sheet"], "loc/inbox/008-U-checks.html")
        self.assertEqual(again["point"], 1)

    def test_unknown_point_changes_nothing(self):
        self.add("One")
        before = (self.project / "loc/inbox/007-U-checks.html").read_text(encoding="utf-8")
        out = self.run_checks("--rate", "--ok", "1", "9", ok=False)
        self.assertIn("no open point 9", out.stderr + out.stdout)
        self.assertEqual((self.project / "loc/inbox/007-U-checks.html").read_text(encoding="utf-8"), before)
        self.assertFalse((self.project / "loc/inbox/done/007-U-checks.html").exists())

    def test_missing_image_is_an_error(self):
        out = self.run_checks("--add", "--title", "x", "--look", "y", "--image", "nope.png", ok=False)
        self.assertIn("image not found", out.stderr + out.stdout)
        self.assertFalse((self.project / "loc/inbox/007-U-checks.html").exists())

    def test_text_is_escaped(self):
        result = self.add("<script>alert(1)</script>")
        text = (self.project / result["sheet"]).read_text(encoding="utf-8")
        self.assertNotIn("<script>alert", text)


class SkillsUseTheSheetTest(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_manual_checks_go_to_the_sheet(self):
        step6 = [line for line in self.read("skills/loc-orchestrate/SKILL.md").splitlines()
                 if line.startswith("6. **Manual check**")][0]
        for part in ("scripts/checks.py --add", "--blocking", "checks.py --rate", "--again", "wait"):
            self.assertIn(part, step6)
        self.assertNotIn("--type deferred", step6)
        self.assertIn("checks.py --list", self.read("skills/loc-qa/SKILL.md"))
        self.assertIn("checks sheet", self.read("skills/loc-planning/SKILL.md"))
        self.assertIn("checks.py --rate", self.read("rules/core.md").split("8. ")[1].split("\n9. ")[0])
        director = self.read("skills/loc-director/SKILL.md")
        self.assertIn("checks.py --list", director.split("## 3. Stop rules")[1].split("## 4.")[0])
        self.assertIn("-U-checks.html", director.split("## 4. Stop report")[1])


if __name__ == "__main__":
    unittest.main()
