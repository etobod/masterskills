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

**Type:** plan
**Status:** open

## Goal
Powitanie w wybranym języku.

## Out of scope
Tłumaczeń spoza listy.

## Not defended against
- none

## Code context
- `app.py:1`

## Milestones

"""
TAIL = """
## Risks and decisions
Brak.
"""

SUITE = """### M1 — test suite
`loc/TEST-PLAN.md` skopiowany z `{path}`.
**Proof:** `python -m unittest -v` → `Ran 1 test`
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
                  claude: str = None, name: str = "007-plan-1-easy-powitania.md") -> tuple:
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
        path = directory / name
        path.write_text(text, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        command = [sys.executable, str(ROOT / "scripts" / "check_plan.py"), str(path)] + (["--ready"] if ready else [])
        result = subprocess.run(command,
                                capture_output=True, text=True, encoding="utf-8", cwd=directory, env=env)
        return result.returncode, json.loads(result.stdout)

    def problems(self, out: dict) -> str:
        return "\n".join(issue["problem"] for issue in out["issues"])

    def defended(self, section: str) -> str:
        text = plan("### M1 — opis\n**No tests:** tylko dokumenty\n**Proof:** `grep x` → `1`\n")
        return text.replace("## Not defended against\n- none\n", section)

    def test_none_defended_against_passes(self):
        code, out = self.run_check(self.defended("## Not defended against\n- none\n"))
        self.assertEqual(code, 0, out)

    def test_missing_defence_section_fails(self):
        code, out = self.run_check(self.defended(""))
        self.assertEqual(code, 1)
        self.assertIn("missing section: ## Not defended against", self.problems(out))

    def test_empty_defence_section_fails(self):
        code, out = self.run_check(self.defended("## Not defended against\nNic.\n"))
        self.assertEqual(code, 1)
        self.assertIn("empty section: ## Not defended against", self.problems(out))

    def test_unfilled_defence_placeholder_fails(self):
        code, out = self.run_check(self.defended(
            "## Not defended against\n- <who or what produces input the code does not defend against>\n"))
        self.assertEqual(code, 1)
        self.assertIn("unfilled placeholder", self.problems(out))

    def test_vague_english_phrase_fails(self):
        for phrase in ("to be confirmed", "we will see", "if it turns out", "maybe", "perhaps", "probably"):
            code, out = self.run_check(plan(f"### M1 — opis\n**No tests:** {phrase} later\n**Proof:** `grep x` → `1`\n"))
            self.assertEqual(code, 1, phrase)
            self.assertIn(phrase, self.problems(out).lower())

    def test_moved_prd_fragment_is_history(self):
        text = plan("### M1 — opis\n**No tests:** tylko dokumenty\n**Proof:** `grep x` → `1`\n").replace(
            "## Risks and decisions", "## PRD fragment\nPrzeniesione z loc/PRD.md 2026-10-15.\n"
            "### Eksport\nFormat do ustalenia, TODO.\n\n## Risks and decisions")
        code, out = self.run_check(text)
        self.assertEqual(code, 0, out)

    def test_criteria_with_tests_pass(self):
        code, out = self.run_check(plan(
            "### M1 — powitanie po polsku\n"
            "Funkcja `greet`.\n"
            "**Criteria:**\n"
            "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"` → `test_app.py::test_polish`\n"
            "- K2 (behaviour): nieznany język daje angielskie powitanie → `test_app.py::test_unknown`\n"
            "**Performer:** auto\n"
            "**Proof:** `python -m unittest test_app` → `OK`\n"))
        self.assertEqual(code, 0, out)

    def test_criterion_without_test_fails_naming_the_milestone(self):
        code, out = self.run_check(plan(
            "### M1 — test suite\n"
            "Smoke test i `loc/TEST-PLAN.md`.\n"
            "**Proof:** `python -m unittest` → `OK`\n\n"
            "### M2 — powitanie\n"
            "**Criteria:**\n"
            "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"`\n"
            "**Performer:** auto\n"
            "**Proof:** `python -m unittest` → `OK`\n"))
        self.assertEqual(code, 1)
        self.assertIn("M2: criterion K1 has no test", self.problems(out))
        self.assertNotIn("M1:", self.problems(out))

    def test_user_performer_without_flag_fails(self):
        code, out = self.run_check(plan(
            "### M1 — wygląd strony\n"
            "**Performer:** user\n"
            "**Proof:** użytkownik potwierdza wygląd → `ok, <data>`\n"))
        self.assertEqual(code, 1)
        self.assertIn("M1: performer must be", self.problems(out))

    def test_manual_criterion_allowed_only_for_the_user(self):
        milestone = ("### M1 — wygląd strony\n"
                     "**Criteria:**\n"
                     "- K1: `layout()` daje jedną kolumnę poniżej 600 px → `test_app.py::test_narrow`\n"
                     "- K2: przycisk jest widoczny na telefonie → manual\n"
                     "**Performer:** {performer}\n"
                     "{manual}"
                     "**Proof:** `python -m unittest test_app` → `OK`\n")
        manual = "**Manual check:** przycisk widoczny na telefonie\n"
        code, out = self.run_check(plan(milestone.format(performer="user (deferrable)", manual=manual)))
        self.assertEqual(code, 0, out)
        code, out = self.run_check(plan(milestone.format(performer="auto", manual="")))
        self.assertEqual(code, 1)
        self.assertIn("M1: criterion K2 has no test", self.problems(out))

    def test_user_performer_still_needs_tests(self):
        """A weak model sent every check to the user; the user checks after the model's own tests."""
        code, out = self.run_check(plan(
            "### M1 — wygląd strony\n"
            "**Criteria:**\n"
            "- K1: przycisk jest widoczny na telefonie → manual\n"
            "**Performer:** user (deferrable)\n"
            "**Manual check:** przycisk widoczny na telefonie\n"
            "**Proof:** `python -m unittest test_app` → `OK`\n"))
        self.assertEqual(code, 1)
        self.assertIn("M1: the user checks after your tests", self.problems(out))
        code, out = self.run_check(plan(
            "### M1 — wygląd strony\n"
            "**Performer:** user (blocking)\n"
            "**Manual check:** przycisk widoczny na telefonie\n"
            "**Proof:** `python -m unittest test_app` → `OK`\n"))
        self.assertEqual(code, 1)
        self.assertIn("M1: no **Criteria:**", self.problems(out))

    def test_user_proof_must_be_a_command(self):
        code, out = self.run_check(plan(
            "### M1 — wygląd strony\n"
            "**Criteria:**\n"
            "- K1: `layout()` daje jedną kolumnę poniżej 600 px → `test_app.py::test_narrow`\n"
            "**Performer:** user (deferrable)\n"
            "**Manual check:** układ na telefonie\n"
            "**Proof:** użytkownik otwiera stronę na telefonie → `ok, <data>`\n"))
        self.assertEqual(code, 1)
        self.assertIn("**Manual check:**, after this proof", self.problems(out))

    def test_manual_check_and_user_performer_go_together(self):
        milestone = ("### M1 — wygląd strony\n"
                     "**Criteria:**\n"
                     "- K1: `layout()` daje jedną kolumnę poniżej 600 px → `test_app.py::test_narrow`\n"
                     "**Performer:** {performer}\n"
                     "{manual}"
                     "**Proof:** `python -m unittest test_app` → `OK`\n")
        code, out = self.run_check(plan(milestone.format(performer="user (blocking)", manual="")))
        self.assertEqual(code, 1)
        self.assertIn("M1: **Performer:** user needs a **Manual check:** line", self.problems(out))
        code, out = self.run_check(plan(milestone.format(performer="auto", manual="**Manual check:** układ na telefonie\n")))
        self.assertEqual(code, 1)
        self.assertIn("M1: **Manual check:** needs **Performer:** user (blocking) or user (deferrable)", self.problems(out))

    def test_combined_check_passes(self):
        code, out = self.run_check(plan(
            "### M1 — epicykle\n"
            "**Criteria:**\n"
            "- K1: `computeFourier([])` zwraca pustą listę bez błędu → `tests/fourier.test.js::empty input`\n"
            "- K2: epicykle rysują kształt płynnie → manual\n"
            "**Performer:** user (deferrable)\n"
            "**Manual check:** epicykle płynnie rysują kształt\n"
            "**Proof:** `node --test` → `pass 1`\n"))
        self.assertEqual(code, 0, out)

    def test_milestone_without_tests_passes_only_with_a_reason(self):
        milestone = ("### M1 — opis w README\n"
                     "Sekcja o powitaniach.\n"
                     "{line}"
                     "**Proof:** `grep -c Powitania README.md` → `1`\n")
        code, out = self.run_check(plan(milestone.format(line="**No tests:** tylko dokumenty\n")))
        self.assertEqual(code, 0, out)
        code, out = self.run_check(plan(milestone.format(line="**No tests:**\n")))
        self.assertEqual(code, 1)
        self.assertIn("M1: **No tests:** needs a reason", self.problems(out))
        code, out = self.run_check(plan(milestone.format(line="")))
        self.assertEqual(code, 1)
        self.assertIn("M1: no **Criteria:**", self.problems(out))

    def test_project_without_suite_starts_with_it(self):
        feature = ("### M{n} — powitanie\n"
                   "**Criteria:**\n"
                   "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"` → `test_app.py::test_polish`\n"
                   "**Proof:** `python -m unittest test_app` → `OK`\n")
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
                   "**Criteria:**\n"
                   "- K1: `greet(\"Ann\", \"pl\")` zwraca `\"Cześć, Ann\"` → `test_app.py::test_polish`\n"
                   "**Proof:** `python -m unittest test_app` → `OK`\n")
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
                     "**Criteria:**\n"
                     "- K1: krzywa jest łososiowa → {test}\n"
                     "**Proof:** `node --test` → `pass 1`\n")
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
                     "**No tests:** tylko szkielet strony\n"
                     "{performer}"
                     "**Proof:** {proof}\n")
        for proof in ("`open fourier.html` → czarny canvas na pełnym ekranie",
                      "`start fourier.html` → `czarny canvas`"):
            with self.subTest(proof=proof):
                code, out = self.run_check(plan(milestone.format(performer="", proof=proof)))
                self.assertEqual(code, 1)
                self.assertIn("M1: ", self.problems(out))
        code, out = self.run_check(plan(milestone.format(
            performer="**Performer:** user (deferrable)\n**Manual check:** czarny canvas na pełnym ekranie\n",
            proof="`node --test` → `pass 1`")))
        self.assertEqual(code, 0, out)

    def test_proof_with_prose_result_quotes_it(self):
        code, out = self.run_check(plan(
            "### M1 — opis\n**No tests:** tylko dokumenty\n"
            "**Proof:** `grep -c x f.html` → znaleziono definicję\n"))
        self.assertEqual(code, 1)
        self.assertIn("found: 'znaleziono definicję'", self.problems(out))
        self.assertIn("`<command>` → `<exact output>`", self.problems(out))

    def test_criterion_must_name_a_test(self):
        milestone = ("### M1 — dwa łańcuchy\n"
                     "**Criteria:**\n"
                     "- K1 (behaviour): x i y z osobnych FFT → {test}\n"
                     "**Proof:** `node --test` → `pass 1`\n")
        code, out = self.run_check(plan(milestone.format(test="`fourier.html`")))
        self.assertEqual(code, 1)
        self.assertIn("M1: criterion K1: `fourier.html` names no test", self.problems(out))
        for test in ("`tests/fft.test.js::rms`", "`parse_test.go::TestParse`", "`spec/app_spec.rb`"):
            with self.subTest(test=test):
                code, out = self.run_check(plan(milestone.format(test=test)))
                self.assertEqual(code, 0, out)

    def ready_plan(self, record: str) -> str:
        return (plan("### M1 — opis\n**No tests:** tylko dokumenty\n**Proof:** `grep x` → `1`\n")
                .replace("**Status:** open", "**Status:** open\n**Source:** loc/inbox/done/001-brainstorm-fourier.md")
                + "\n## Plan gate\n" + record + "\n## Resolution\n")

    def test_ready_needs_a_recorded_gate(self):
        for record in ("", "<zapis rund bramki: runda, wynik `check_plan.py`>\n"):
            with self.subTest(record=record):
                code, out = self.run_check(self.ready_plan(record), ready=True)
                self.assertEqual(code, 1)
                self.assertIn("## Plan gate records no round", self.problems(out))
        done = self.ready_plan("- round 1: skan czysty, krytyk bez uwag blokujących\n")
        code, out = self.run_check(done, ready=True)
        self.assertEqual(code, 0, out)
        code, out = self.run_check(self.ready_plan(""))
        self.assertEqual(code, 0, out)

    def test_ready_needs_the_input_closed(self):
        text = self.ready_plan("- round 1: skan czysty\n")
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
                self.assertIn("write `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md`", self.problems(out))

    def test_missing_plugin_path_fails(self):
        """A weak model fixed the prefix wrongly; the path must exist in the plugin."""
        code, out = self.run_check(plan(SUITE.format(path="${CLAUDE_PLUGIN_ROOT}/masterskills/templates/loc/TEST-PLAN.md")))
        self.assertEqual(code, 1)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/masterskills/templates/loc/TEST-PLAN.md does not exist", self.problems(out))
        self.assertIn("write `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md`", self.problems(out))

    def test_plugin_root_variable_passes(self):
        code, out = self.run_check(plan(SUITE.format(path="${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md")))
        self.assertEqual(code, 0, out)


REVIEW = """# 003 — Review of the greeting

**Type:** review
**Status:** open
**Created:** 2026-10-16 10:00
**Source:** HEAD

## Scope
app.py

## Findings
- **[Blocking]** `app.py:3` — one chain for both axes → two FFTs
- **[Non-blocking]** `app.py:28` — the error display is never updated → compute RMS
- **[Suggestion]** `app.py:90` — `trail.shift()` is O(n) → ring buffer
- **[Non-blocking]** `app.py:40` — the button does nothing → draw the path

## Resolution
{resolution}
"""

REVIEWED_PLAN = """# 004 — Fix the review

**Type:** plan
**Status:** open
**Source:** {source}

## Goal
The review findings are fixed.

## Out of scope
- Input findings without a fix verdict: ## Review notes.

## Not defended against
- none

## Code context
- `app.py:3`

## Milestones

### M1 — two chains
Fixes 003 #1.{extra}
**No tests:** docs only
**Proof:** `grep x` → `1`

## Risks and decisions
- none

## Review notes
{notes}
"""

ALL_NOTES = ("- enough (planning): 003 #2 `app.py:28` — no display. Reason: cosmetic [Goal 1]\n"
             "- suggestion (planning): 003 #3 `app.py:90` — O(n) shift\n")


class PlanNameTest(unittest.TestCase):
    run_check = CheckPlanTest.run_check
    problems = CheckPlanTest.problems
    GOOD = plan("### M1 — powitanie\n**No tests:** documents only\n**Proof:** `python -m unittest` → `OK`\n")

    def test_name_has_the_difficulty(self):
        for name, ok in (("007-plan-powitania.md", False), ("007-plan-easy-powitania.md", False),
                         ("007-plan-2-hard-powitania.md", True), ("007-plan-1-medium-x.md", True),
                         ("007-plan-1-easy.md", False), ("007-plan-1-powitania.md", False)):
            with self.subTest(name=name):
                code, out = self.run_check(self.GOOD, name=name)
                self.assertEqual("file name" in self.problems(out), not ok, out)

    def test_ready_accepts_old_names(self):
        code, out = self.run_check(self.GOOD, name="007-plan-powitania.md", ready=True)
        self.assertNotIn("file name", self.problems(out))

    def test_planning_names_the_difficulty(self):
        text = (ROOT / "skills" / "loc-planning" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('--slug "<group>-<difficulty>-<topic>"', text)


class ReviewSourceTest(unittest.TestCase):
    """A plan made from a review accounts for every finding of that review."""

    def run_plan(self, notes: str, extra: str = "", resolution: str = "<empty until handled>",
                 folder: str = "loc/inbox") -> tuple:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, directory, True)
        review = directory / folder / "003-review-greeting.md"
        review.parent.mkdir(parents=True)
        review.write_text(REVIEW.format(resolution=resolution), encoding="utf-8")
        path = directory / "loc" / "inbox" / "004-plan-1-easy-fix.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        source = f"{folder}/003-review-greeting.md"
        path.write_text(REVIEWED_PLAN.format(source=source, notes=notes, extra=extra), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_plan.py"), str(path)],
                                capture_output=True, text=True, encoding="utf-8", cwd=directory, env=env)
        out = json.loads(result.stdout)
        return result.returncode, "\n".join(issue["problem"] for issue in out["issues"])

    def test_unjudged_finding_fails(self):
        code, problems = self.run_plan(ALL_NOTES)
        self.assertEqual(code, 1)
        self.assertIn("003 #4", problems)
        self.assertIn("judge", problems)
        self.assertNotIn("003 #2", problems)

    def test_every_finding_accounted_passes(self):
        code, problems = self.run_plan(ALL_NOTES, resolution="- 003 #4 already fixed in `app.py:40`")
        self.assertEqual(code, 0, problems)
        code, problems = self.run_plan(ALL_NOTES, extra=" Also 003 #4.")
        self.assertEqual(code, 0, problems)

    def test_suggestion_in_milestone_fails(self):
        code, problems = self.run_plan(ALL_NOTES, extra=" Also 003 #4 and 003 #3.")
        self.assertEqual(code, 1)
        self.assertIn("003 #3", problems)
        self.assertIn("Suggestion", problems)

    def test_review_in_done_is_found(self):
        code, problems = self.run_plan(ALL_NOTES, folder="loc/inbox/done")
        self.assertEqual(code, 1)
        self.assertIn("003 #4", problems)


if __name__ == "__main__":
    unittest.main()


class DecisionQuestionTest(unittest.TestCase):
    """A decision the plan proposes waits in a question file, not only in the report."""

    def run_plan(self, risks: str, prd: str = "## Decisions\n- D-02: one URL per thread. Reason: x. (2026-10-01)\n",
                 fragment: str = "") -> tuple:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, directory, True)
        (directory / "loc").mkdir()
        (directory / "loc" / "PRD.md").write_text("# PRD\n\n" + prd, encoding="utf-8")
        text = plan("### M1 — opis\n**No tests:** tylko dokumenty\n**Proof:** `grep x` → `1`\n")
        text = text.replace("## Risks and decisions\nBrak.\n", f"## Risks and decisions\n{risks}\n{fragment}")
        path = directory / "007-plan-1-easy-powitania.md"
        path.write_text(text, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_plan.py"), str(path)],
                                capture_output=True, text=True, encoding="utf-8", cwd=directory, env=env)
        out = json.loads(result.stdout)
        return result.returncode, "\n".join(issue["problem"] for issue in out["issues"])

    def test_new_decision_without_a_question_fails(self):
        code, problems = self.run_plan("- D-05 (proposed): the rule lives in sources.json.")
        self.assertEqual(code, 1)
        self.assertIn("D-05", problems)
        self.assertIn("question", problems)

    def test_new_decision_with_a_question_passes(self):
        code, problems = self.run_plan("- D-05 (proposed) → loc/inbox/018-question-decisions.md, interim: yes.")
        self.assertEqual(code, 0, problems)

    def test_recorded_or_moved_decision_passes(self):
        code, problems = self.run_plan("- D-02 stays.")
        self.assertEqual(code, 0, problems)
        code, problems = self.run_plan("- D-02 stays.", fragment="## PRD fragment\n- D-01: old line.\n")
        self.assertEqual(code, 0, problems)


class MilestoneLimitTest(unittest.TestCase):
    run_check = CheckPlanTest.run_check
    problems = CheckPlanTest.problems
    SUITE = ("### M1 — test suite\nFramework, command, smoke test, `loc/TEST-PLAN.md`.\n"
             "**Proof:** `python -m unittest` → `OK`\n")

    def milestones(self, count: int, first: int = 1) -> str:
        return "".join(f"### M{n} — part {n}\n**No tests:** documents only\n**Proof:** `python -m unittest` → `OK`\n"
                       for n in range(first, first + count))

    def over(self, difficulty: str, count: int, suite: bool = False, ready: bool = False) -> bool:
        body = (self.SUITE + self.milestones(count, 2)) if suite else self.milestones(count)
        code, out = self.run_check(plan(body), name=f"007-plan-1-{difficulty}-x.md", ready=ready)
        return "milestones, the limit" in self.problems(out)

    def test_limit_follows_the_difficulty(self):
        for difficulty, count, over in (("hard", 4, True), ("hard", 3, False), ("easy", 6, False),
                                        ("easy", 7, True), ("medium", 5, True), ("medium", 4, False)):
            with self.subTest(difficulty=difficulty, count=count):
                self.assertEqual(self.over(difficulty, count), over)

    def test_suite_milestone_is_not_counted(self):
        self.assertFalse(self.over("hard", 3, suite=True))
        self.assertTrue(self.over("hard", 4, suite=True))

    def test_ready_skips_the_limit(self):
        self.assertFalse(self.over("hard", 5, ready=True))

    def test_planning_states_the_limits(self):
        text = (ROOT / "skills" / "loc-planning" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`easy` 6, `medium` 4, `hard` 3", text)
