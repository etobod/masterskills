"""Tests for scripts/check_plan.py: acceptance criteria and performer in milestones."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch files stay inside the repository (CLAUDE.md rule 1), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"

HEAD = """# 007 — Plan: powitania

**Typ:** plan
**Status:** otwarte

## Cel
Powitanie w wybranym języku.

## Czego nie robimy
Tłumaczeń spoza listy.

## Kontekst z kodu
- `app.py:1`

## Kamienie milowe

"""
TAIL = """
## Ryzyka i decyzje
Brak.
"""


def plan(milestones: str) -> str:
    return HEAD + milestones + TAIL


class CheckPlanTest(unittest.TestCase):
    def run_check(self, text: str) -> tuple:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, directory, True)
        path = directory / "007-plan-powitania.md"
        path.write_text(text, encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_plan.py"), str(path)],
                                capture_output=True, text=True, encoding="utf-8")
        return result.returncode, json.loads(result.stdout)

    def problems(self, out: dict) -> str:
        return "\n".join(issue["problem"] for issue in out["issues"])

    def test_criteria_with_tests_pass(self):
        code, out = self.run_check(plan(
            "### M1 — powitanie po polsku\n"
            "Funkcja `greet`.\n"
            "**Kryteria:**\n"
            "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"` → `test_app.py::test_polish`\n"
            "- K2 (zachowanie): nieznany język daje angielskie powitanie → `test_app.py::test_unknown`\n"
            "**Wykonawca:** auto\n"
            "**Dowód:** `python -m unittest test_app` → `OK`\n"))
        self.assertEqual(code, 0, out)

    def test_criterion_without_test_fails_naming_the_milestone(self):
        code, out = self.run_check(plan(
            "### M1 — zestaw testów\n"
            "Smoke test.\n"
            "**Dowód:** `python -m unittest` → `OK`\n\n"
            "### M2 — powitanie\n"
            "**Kryteria:**\n"
            "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"`\n"
            "**Wykonawca:** auto\n"
            "**Dowód:** `python -m unittest` → `OK`\n"))
        self.assertEqual(code, 1)
        self.assertIn("M2: criterion K1 has no test", self.problems(out))
        self.assertNotIn("M1:", self.problems(out))

    def test_user_performer_without_flag_fails(self):
        code, out = self.run_check(plan(
            "### M1 — wygląd strony\n"
            "**Wykonawca:** użytkownik\n"
            "**Dowód:** użytkownik potwierdza wygląd → `ok, <data>`\n"))
        self.assertEqual(code, 1)
        self.assertIn("M1: performer must be", self.problems(out))

    def test_manual_criterion_allowed_only_for_the_user(self):
        milestone = ("### M1 — wygląd strony\n"
                     "**Kryteria:**\n"
                     "- K1: przycisk jest widoczny na telefonie → ręcznie\n"
                     "**Wykonawca:** {performer}\n"
                     "**Dowód:** potwierdzenie użytkownika z datą → `ok`\n")
        code, out = self.run_check(plan(milestone.format(performer="użytkownik (odkładalny)")))
        self.assertEqual(code, 0, out)
        code, out = self.run_check(plan(milestone.format(performer="auto")))
        self.assertEqual(code, 1)
        self.assertIn("M1: criterion K1 has no test", self.problems(out))

    def test_plan_without_criteria_passes(self):
        code, out = self.run_check(plan(
            "### M1 — opis w README\n"
            "Sekcja o powitaniach.\n"
            "**Dowód:** `grep -c Powitania README.md` → `1`\n"))
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
