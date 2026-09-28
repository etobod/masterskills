"""Tests for scripts/check_state.py: the plan execution state file."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch projects stay inside the repository (CLAUDE.md rule 1), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def state(gates: dict) -> dict:
    return {
        "plan": "loc/inbox/007-plan-powitania.md",
        "mode": "inline",
        "milestone": 1,
        "phase": "proof",
        "milestones": [{"id": "M1", "status": "in_progress", "start": "abc1234", "end": None}],
        "gates": gates,
        "deviations": [],
        "next_action": "Run the M1 proof: python -m unittest; expected OK",
        "updated": "2026-09-28 16:00",
    }


PLAN_WITH_CRITERIA = """### M1 — powitanie
**Kryteria:**
- K1: `greet("Ann", "pl")` zwraca `"Cześć, Ann"` → `test_app.py::GreetTest::test_polish`
**Dowód:** `python -m unittest` → `OK`
"""


class CheckStateTest(unittest.TestCase):
    def run_check(self, data: dict, plan: str = None) -> tuple:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        path = project / "loc" / "state" / "007.json"
        path.parent.mkdir(parents=True)
        if plan is not None:
            (project / "loc" / "inbox" / "done").mkdir(parents=True)
            (project / "loc" / "inbox" / "done" / "007-plan-powitania.md").write_text(plan, encoding="utf-8")
        path.write_text(json.dumps(data), encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_state.py"), str(path)],
                                capture_output=True, text=True, encoding="utf-8")
        return result.returncode, json.loads(result.stdout)

    def test_red_gate_with_output_is_valid(self):
        red = {"rounds": 1, "passed": True, "stuck": None,
               "output": "AssertionError: 'Hello, Ann' != 'Cześć, Ann'"}
        code, out = self.run_check(state({"M1/red": red, "M1/proof": {"rounds": 1, "passed": False, "stuck": None}}))
        self.assertEqual(code, 0, out)

    def test_passed_red_gate_needs_the_output(self):
        code, out = self.run_check(state({"M1/red": {"rounds": 1, "passed": True, "stuck": None}}))
        self.assertEqual(code, 1)
        self.assertIn("gates.M1/red.output", "\n".join(out["problems"]))

    def test_unknown_gate_is_rejected(self):
        code, out = self.run_check(state({"M1/green": {"rounds": 1, "passed": True, "stuck": None}}))
        self.assertEqual(code, 1)
        self.assertIn("unknown gate", "\n".join(out["problems"]))

    def test_red_gate_of_a_missing_milestone_is_rejected(self):
        code, out = self.run_check(state({"M2/red": {"rounds": 0, "passed": False, "stuck": None}}))
        self.assertEqual(code, 1)
        self.assertIn("no such milestone", "\n".join(out["problems"]))

    def finished(self, phase: str, gates: dict) -> dict:
        data = state(gates)
        data.update(plan="loc/inbox/done/007-plan-powitania.md", phase=phase)
        data["milestones"][0].update(status="done", end="def5678")
        return data

    def test_qa_phase_is_valid(self):
        code, out = self.run_check({**state({"qa": {"rounds": 1, "passed": False, "stuck": None}}), "phase": "qa"})
        self.assertEqual(code, 0, out)

    def test_journal_without_qa_gate_fails_when_the_plan_has_criteria(self):
        code, out = self.run_check(self.finished("journal", {}), PLAN_WITH_CRITERIA)
        self.assertEqual(code, 1)
        self.assertIn("gates.qa", "\n".join(out["problems"]))

    def test_journal_after_passed_qa_is_valid(self):
        code, out = self.run_check(self.finished("journal", {"qa": {"rounds": 2, "passed": True, "stuck": None}}),
                                   PLAN_WITH_CRITERIA)
        self.assertEqual(code, 0, out)

    def test_journal_without_qa_is_valid_for_a_plan_without_criteria(self):
        code, out = self.run_check(self.finished("done", {}), "### M1 — opis\n**Dowód:** `grep x` → `1`\n")
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
