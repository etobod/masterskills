"""Tests for scripts/check_plan.py: acceptance criteria and performer in milestones."""

import json
import os
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

## Nie bronimy przed
- brak

## Kontekst z kodu
- `app.py:1`

## Kamienie milowe

"""
TAIL = """
## Ryzyka i decyzje
Brak.
"""

SUITE = """### M1 — zestaw testów
`loc/TEST-PLAN.md` skopiowany z `{path}`.
**Dowód:** `python -m unittest -v` → `Ran 1 test`
"""

COMMANDS = """# app

## Commands
<!-- Exact build, test, lint and run commands. Skills use these and never guess. -->
{command}

## Invariants
- two chains
"""

def plan(milestones: str) -> str:
    return HEAD + milestones + TAIL


class CheckPlanTest(unittest.TestCase):
    def run_check(self, text: str, suite: bool = True, ready: bool = False, files: tuple = (),
                  claude: str = None) -> tuple:
        """Check `text` as a plan of a project that has a test suite (`loc/TEST-PLAN.md` and a test
        command in `CLAUDE.md`) or not; `files` are created in the project first, `claude` is its
        `CLAUDE.md`, `ready` adds `--ready`."""
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, directory, True)
        if suite:
            (directory / "loc").mkdir()
            (directory / "loc" / "TEST-PLAN.md").write_text("# TEST-PLAN\n", encoding="utf-8")
            (directory / "CLAUDE.md").write_text(COMMANDS.format(command="`python -m unittest`"),
                                                 encoding="utf-8")
        for rel in files:
            (directory / rel).parent.mkdir(parents=True, exist_ok=True)
            (directory / rel).write_text("# 001\n", encoding="utf-8")
        if claude is not None:
            (directory / "CLAUDE.md").write_text(claude, encoding="utf-8")
        path = directory / "007-plan-powitania.md"
        path.write_text(text, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        command = [sys.executable, str(ROOT / "scripts" / "check_plan.py"), str(path)] + (["--ready"] if ready else [])
        result = subprocess.run(command,
                                capture_output=True, text=True, encoding="utf-8", cwd=directory, env=env)
        return result.returncode, json.loads(result.stdout)

    def problems(self, out: dict) -> str:
        return "\n".join(issue["problem"] for issue in out["issues"])

    def defended(self, section: str) -> str:
        text = plan("### M1 — opis\n**Bez testów:** tylko dokumenty\n**Dowód:** `grep x` → `1`\n")
        return text.replace("## Nie bronimy przed\n- brak\n", section)

    def test_none_defended_against_passes(self):
        code, out = self.run_check(self.defended("## Nie bronimy przed\n- brak\n"))
        self.assertEqual(code, 0, out)

    def test_missing_defence_section_fails(self):
        code, out = self.run_check(self.defended(""))
        self.assertEqual(code, 1)
        self.assertIn("missing section: ## Nie bronimy przed", self.problems(out))

    def test_empty_defence_section_fails(self):
        code, out = self.run_check(self.defended("## Nie bronimy przed\nNic.\n"))
        self.assertEqual(code, 1)
        self.assertIn("empty section: ## Nie bronimy przed", self.problems(out))

    def test_unfilled_defence_placeholder_fails(self):
        code, out = self.run_check(self.defended(
            "## Nie bronimy przed\n- <kto albo co wytwarza wejście, przed którym kod nie broni>\n"))
        self.assertEqual(code, 1)
        self.assertIn("unfilled placeholder", self.problems(out))

    def test_moved_prd_fragment_is_history(self):
        text = plan("### M1 — opis\n**Bez testów:** tylko dokumenty\n**Dowód:** `grep x` → `1`\n").replace(
            "## Ryzyka i decyzje", "## Fragment PRD\nPrzeniesione z loc/PRD.md 2026-10-15.\n"
            "### Eksport\nFormat do ustalenia, TODO.\n\n## Ryzyka i decyzje")
        code, out = self.run_check(text)
        self.assertEqual(code, 0, out)

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
            "Smoke test i `loc/TEST-PLAN.md`.\n"
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

    def test_milestone_without_tests_passes_only_with_a_reason(self):
        milestone = ("### M1 — opis w README\n"
                     "Sekcja o powitaniach.\n"
                     "{line}"
                     "**Dowód:** `grep -c Powitania README.md` → `1`\n")
        code, out = self.run_check(plan(milestone.format(line="**Bez testów:** tylko dokumenty\n")))
        self.assertEqual(code, 0, out)
        code, out = self.run_check(plan(milestone.format(line="**Bez testów:**\n")))
        self.assertEqual(code, 1)
        self.assertIn("M1: **Bez testów:** needs a reason", self.problems(out))
        code, out = self.run_check(plan(milestone.format(line="")))
        self.assertEqual(code, 1)
        self.assertIn("M1: no **Kryteria:**", self.problems(out))

    def test_project_without_suite_starts_with_it(self):
        feature = ("### M{n} — powitanie\n"
                   "**Kryteria:**\n"
                   "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"` → `test_app.py::test_polish`\n"
                   "**Dowód:** `python -m unittest test_app` → `OK`\n")
        code, out = self.run_check(plan(feature.format(n=1)), suite=False)
        self.assertEqual(code, 1)
        self.assertIn("M1 must set up the test suite", self.problems(out))
        setup = SUITE.format(path="${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md")
        code, out = self.run_check(plan(setup + "\n" + feature.format(n=2)), suite=False)
        self.assertEqual(code, 0, out)
        code, out = self.run_check(plan(feature.format(n=1)), suite=True)
        self.assertEqual(code, 0, out)

    def test_suite_needs_a_test_command(self):
        feature = ("### M1 — powitanie\n"
                   "**Kryteria:**\n"
                   "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"` → `test_app.py::test_polish`\n"
                   "**Dowód:** `python -m unittest test_app` → `OK`\n")
        stub = ("loc/TEST-PLAN.md",)
        for command in ("", "`open fourier.html`"):
            with self.subTest(command=command):
                code, out = self.run_check(plan(feature), suite=False, files=stub,
                                           claude=COMMANDS.format(command=command))
                self.assertEqual(code, 1)
                self.assertIn("M1 must set up the test suite", self.problems(out))
                self.assertIn("do not create loc/TEST-PLAN.md while planning", self.problems(out))
        code, out = self.run_check(plan(feature), suite=False, files=stub,
                                   claude=COMMANDS.format(command="`python -m unittest`"))
        self.assertEqual(code, 0, out)


    def test_shell_check_is_not_a_test(self):
        milestone = ("### M1 — kolor krzywej\n"
                     "**Kryteria:**\n"
                     "- K1: krzywa jest łososiowa → {test}\n"
                     "**Dowód:** `node --test` → `pass 1`\n")
        for test in ('`grep "salmon" fourier.html`', "`test -f parse_svg.html && open parse_svg.html`",
                     "`open butterfly.html`", "`node --test | grep pass`"):
            with self.subTest(test=test):
                code, out = self.run_check(plan(milestone.format(test=test)))
                self.assertEqual(code, 1)
                self.assertIn("is a shell check, not a test", self.problems(out))
        code, out = self.run_check(plan(milestone.format(test="`tests/curve.test.js::kolor łososiowy`")))
        self.assertEqual(code, 0, out)

    def test_automatic_proof_must_be_checkable(self):
        milestone = ("### M1 — pusta animacja\n"
                     "**Bez testów:** tylko szkielet strony\n"
                     "{performer}"
                     "**Dowód:** {proof}\n")
        for proof in ("`open fourier.html` → czarny canvas na pełnym ekranie",
                      "`start fourier.html` → `czarny canvas`"):
            with self.subTest(proof=proof):
                code, out = self.run_check(plan(milestone.format(performer="", proof=proof)))
                self.assertEqual(code, 1)
                self.assertIn("M1: ", self.problems(out))
        code, out = self.run_check(plan(milestone.format(
            performer="**Wykonawca:** użytkownik (odkładalny)\n",
            proof="użytkownik otwiera `fourier.html` i widzi czarny canvas → `ok, <data>`")))
        self.assertEqual(code, 0, out)

    def test_proof_with_prose_result_quotes_it(self):
        code, out = self.run_check(plan(
            "### M1 — opis\n**Bez testów:** tylko dokumenty\n"
            "**Dowód:** `grep -c x f.html` → znaleziono definicję\n"))
        self.assertEqual(code, 1)
        self.assertIn("found: 'znaleziono definicję'", self.problems(out))
        self.assertIn("`<command>` → `<exact output>`", self.problems(out))

    def test_criterion_must_name_a_test(self):
        milestone = ("### M1 — dwa łańcuchy\n"
                     "**Kryteria:**\n"
                     "- K1 (zachowanie): x i y z osobnych FFT → {test}\n"
                     "**Dowód:** `node --test` → `pass 1`\n")
        code, out = self.run_check(plan(milestone.format(test="`fourier.html`")))
        self.assertEqual(code, 1)
        self.assertIn("M1: criterion K1: `fourier.html` names no test", self.problems(out))
        for test in ("`tests/fft.test.js::rms`", "`parse_test.go::TestParse`", "`spec/app_spec.rb`"):
            with self.subTest(test=test):
                code, out = self.run_check(plan(milestone.format(test=test)))
                self.assertEqual(code, 0, out)

    def ready_plan(self, record: str) -> str:
        return (plan("### M1 — opis\n**Bez testów:** tylko dokumenty\n**Dowód:** `grep x` → `1`\n")
                .replace("**Status:** otwarte", "**Status:** otwarte\n**Źródło:** loc/inbox/done/001-brainstorm-fourier.md")
                + "\n## Bramka planu\n" + record + "\n## Rozstrzygnięcie\n")

    def test_ready_needs_a_recorded_gate(self):
        for record in ("", "<zapis rund bramki: runda, wynik `check_plan.py`>\n"):
            with self.subTest(record=record):
                code, out = self.run_check(self.ready_plan(record), ready=True)
                self.assertEqual(code, 1)
                self.assertIn("## Bramka planu records no round", self.problems(out))
        done = self.ready_plan("- runda 1: skan czysty, krytyk bez uwag blokujących\n")
        code, out = self.run_check(done, ready=True)
        self.assertEqual(code, 0, out)
        code, out = self.run_check(self.ready_plan(""))
        self.assertEqual(code, 0, out)

    def test_ready_needs_the_input_closed(self):
        text = self.ready_plan("- runda 1: skan czysty\n")
        code, out = self.run_check(text, ready=True, files=("loc/inbox/001-brainstorm-fourier.md",))
        self.assertEqual(code, 1)
        self.assertIn("input loc/inbox/001-brainstorm-fourier.md is still open", self.problems(out))
        code, out = self.run_check(text, ready=True, files=("loc/inbox/done/001-brainstorm-fourier.md",))
        self.assertEqual(code, 0, out)

    def test_expanded_plugin_path_fails(self):
        for path in (f"{ROOT.as_posix()}/templates/loc/TEST-PLAN.md", str(ROOT / "templates" / "loc" / "TEST-PLAN.md")):
            with self.subTest(path=path):
                code, out = self.run_check(plan(SUITE.format(path=path)))
                self.assertEqual(code, 1)
                self.assertIn("plugin path in the plan", self.problems(out))

    def test_plugin_root_variable_passes(self):
        code, out = self.run_check(plan(SUITE.format(path="${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md")))
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
