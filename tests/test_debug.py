"""The `loc-debug` skill: a reported bug, from a reproduction to its cause."""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"
SKILL = ROOT / "skills" / "loc-debug" / "SKILL.md"


class DebugSkillTest(unittest.TestCase):
    def text(self) -> str:
        return SKILL.read_text(encoding="utf-8")

    def test_front_matter(self):
        front = re.match(r"^---\n(.*?)\n---\n", self.text(), re.S).group(1)
        self.assertRegex(front, r"(?m)^name: loc-debug$")
        self.assertRegex(front, r"(?m)^description: Use when .*\(e\.g\. ")
        self.assertRegex(front, r"(?m)^argument-hint: ")

    def test_steps_come_in_order(self):
        headings = re.findall(r"(?m)^## (\d)\. (.+)$", self.text())
        names = [name.lower() for _, name in headings]
        order = ["reproduce", "failing test", "hypotheses", "cause", "record"]
        positions = [next(i for i, n in enumerate(names) if word in n) for word in order]
        self.assertEqual(positions, sorted(positions), names)

    def test_rules(self):
        text = self.text()
        self.assertIn("never fix on a guess", text.lower())
        for part in ("3 rounds", "`deferred`", "loc/tmp/", "loc/PATTERNS.md",
                     "loc-journal", "CLAUDE.md", "loc/TEST-PLAN.md", "e.g."):
            self.assertIn(part, text)

    def test_readme_lists_it(self):
        self.assertRegex((ROOT / "README.md").read_text(encoding="utf-8"), r"(?m)^\| `loc-debug` \| ")

    def test_opencode_builds_it(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        subprocess.run([sys.executable, "-B", str(ROOT / "opencode" / "build.py"), "--out", str(out)],
                       check=True, capture_output=True)
        self.assertTrue((out / "skills" / "loc-debug" / "SKILL.md").is_file())
        self.assertTrue((out / "commands" / "loc-debug.md").is_file())


if __name__ == "__main__":
    unittest.main()
