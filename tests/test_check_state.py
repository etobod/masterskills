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


class CheckStateTest(unittest.TestCase):
    def run_check(self, data: dict) -> tuple:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        path = project / "loc" / "state" / "007.json"
        path.parent.mkdir(parents=True)
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


if __name__ == "__main__":
    unittest.main()
