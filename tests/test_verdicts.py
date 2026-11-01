"""Every review finding gets a verdict before the judge: confirmed, needs_validation or rejected."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"
VERDICTS = ("`confirmed`", "`needs_validation`", "`rejected`")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


class VerdictTextTest(unittest.TestCase):
    def test_gates_defines_the_verdicts(self):
        body = section(read("skills/loc-orchestrate/references/gates.md"), "## Verdicts")
        for part in VERDICTS + ("judge", "unconfirmed", "e.g.", "one line"):
            self.assertIn(part, body)

    def test_skills_give_verdicts_before_the_judge(self):
        orchestrate = read("skills/loc-orchestrate/SKILL.md")
        step5 = [line for line in orchestrate.splitlines() if line.startswith("5. **Code-review gate**")][0]
        self.assertIn("verdict", step5)
        merge = section(read("skills/loc-review/SKILL.md"), "## 3. Merge")
        self.assertIn("verdict", merge)
        self.assertIn('"Verdicts"', merge)

    def test_state_reference_names_the_field(self):
        text = read("skills/loc-orchestrate/references/state.md")
        self.assertIn('"verdicts"', text)
        self.assertIn("needs_validation", text)


def state(gates: dict) -> dict:
    return {
        "plan": "loc/inbox/007-plan-greeting.md",
        "mode": "inline",
        "milestone": 1,
        "phase": "code-review",
        "milestones": [{"id": "M1", "status": "in_progress", "start": "abc1234", "end": "abc1235"}],
        "gates": gates,
        "deviations": [],
        "next_action": "Run the M1 code review",
        "updated": "2026-11-01 10:00",
    }


class VerdictStateTest(unittest.TestCase):
    def check(self, gates: dict) -> list:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        path = project / "loc" / "state" / "007.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(state(gates)), encoding="utf-8")
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_state.py"), str(path)],
                             capture_output=True, text=True, encoding="utf-8")
        return [p for p in json.loads(out.stdout)["problems"] if "verdicts" in p]

    def gate(self, verdicts) -> dict:
        return {"rounds": 1, "passed": False, "stuck": None, "verdicts": verdicts}

    def test_counts_are_accepted_on_review_gates(self):
        good = {"confirmed": 2, "needs_validation": 1, "rejected": 0}
        self.assertEqual(self.check({"M1/code-review": self.gate(good), "final-review": self.gate(good)}), [])

    def test_bad_shapes_are_rejected(self):
        for bad in ({"confirmed": 1}, {"confirmed": 1, "needs_validation": 0, "rejected": -1},
                    {"confirmed": 1, "needs_validation": 0, "rejected": 0, "maybe": 1},
                    {"confirmed": True, "needs_validation": 0, "rejected": 0}, [1, 0, 0]):
            self.assertTrue(self.check({"M1/code-review": self.gate(bad)}), bad)

    def test_other_gates_have_none(self):
        good = {"confirmed": 1, "needs_validation": 0, "rejected": 0}
        self.assertTrue(self.check({"M1/proof": self.gate(good)}))


if __name__ == "__main__":
    unittest.main()
