"""Ideas taken from other skill packs: budgets, the "does this code need to exist" ladder,
the grill mode of brainstorming and the marking of diagram elements."""

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def front(text: str) -> str:
    return re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)


def measure():
    spec = importlib.util.spec_from_file_location("measure", ROOT / "scripts" / "measure.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BudgetTest(unittest.TestCase):
    def test_raised_limits(self):
        overrides = measure().OVERRIDES
        self.assertEqual(overrides["skills/loc-orchestrate/SKILL.md"], 1300)
        self.assertEqual(overrides["skills/loc-review/SKILL.md"], 900)
        self.assertEqual(overrides["skills/loc-diagram/SKILL.md"], 850)
        self.assertEqual(overrides["skills/loc-planning/SKILL.md"], 2650)
        self.assertEqual(overrides["skills/loc-qa/SKILL.md"], 1000)
        self.assertEqual(overrides["agents/judge.md"], 650)
        self.assertEqual(overrides["agents/rubber-duck.md"], 650)


class LadderTest(unittest.TestCase):
    def implement_step(self) -> str:
        text = read("skills/loc-orchestrate/SKILL.md")
        return re.search(r"2\. \*\*Implement\*\*.*?\n3\. ", text, re.S).group(0)

    def test_orchestrate_climbs_the_ladder_before_code(self):
        step = self.implement_step()
        for rung in ("already in the project", "standard library", "platform",
                     "installed dependency", "one line"):
            self.assertIn(rung, step)
        for kept in ("validation", "error handling", "security", "accessibility"):
            self.assertIn(kept, step)

    def test_subagent_gets_the_ladder(self):
        step = self.implement_step()
        subagent = re.search(r"\*subagent\*:.*", step).group(0)
        self.assertIn("ladder", subagent)

    def test_code_review_flags_code_that_already_exists(self):
        for rel in ("skills/loc-orchestrate/SKILL.md", "skills/loc-review/SKILL.md"):
            text = read(rel)
            calls = re.findall(r'Skill\(skill: "code-review", args: "[^"]*"\)', text)
            self.assertTrue(calls, rel)
            self.assertTrue(
                all("already provide" in call for call in calls),
                f"{rel}: every code-review call asks for code the project or platform already provides",
            )


class GrillTest(unittest.TestCase):
    def test_brainstorm_has_a_grill_mode(self):
        text = read("skills/loc-brainstorm/SKILL.md")
        self.assertIn("## Grill mode", text)
        section = text.split("## Grill mode", 1)[1].split("\n## ", 1)[0]
        self.assertIn("grill me", section)
        self.assertIn("przepytaj mnie", section)
        self.assertIn("one question at a time", section)
        self.assertIn("recommend", section)
        self.assertIn("## Open", section)
        self.assertIn("grill me", front(text))


class DiagramMarksTest(unittest.TestCase):
    def test_every_element_is_read_or_marked(self):
        text = read("skills/loc-diagram/SKILL.md")
        self.assertIn("every box and every arrow", text)
        self.assertIn("inferred", text)
        self.assertIn("`?`", text)


class TrackedInputsTest(unittest.TestCase):
    """A plan never gitignores a file its proofs, tests or manual checks need."""

    def test_planning_keeps_test_inputs_in_git(self):
        text = (ROOT / "skills" / "loc-planning" / "SKILL.md").read_text(encoding="utf-8")
        rule = [line for line in text.splitlines() if "`.gitignore`" in line and "proof" in line]
        self.assertTrue(rule, "no rule about test inputs in .gitignore")
        for part in ("test", "manual check", "in git", "made by the test"):
            self.assertIn(part, rule[0])


class LeanReviewTest(unittest.TestCase):
    """A reviewer runs once per round, and the final code review skips what the milestones reviewed."""

    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_reviewers_run_once_per_round(self):
        review = self.read("skills/loc-review/SKILL.md").split("## 2. Review, in parallel", 1)[1].split("\n## ", 1)[0]
        step5 = [line for line in self.read("skills/loc-orchestrate/SKILL.md").splitlines()
                 if line.startswith("5. **Code-review gate**")][0]
        for text in (review, step5):
            self.assertIn("once per round", text)
            self.assertIn("never a relaunch", text)

    def test_final_code_review_skips_reviewed_milestones(self):
        review = self.read("skills/loc-review/SKILL.md").split("## 2. Review, in parallel", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Orchestrated", review)
        self.assertIn("how the milestones work together", review)
        self.assertIn("after the last milestone's `end`", review)


class AgentAnswerTest(unittest.TestCase):
    """An agent ends with its report alone, and says so when it found nothing."""

    def test_every_agent_ends_with_its_report(self):
        files = sorted((ROOT / "agents").glob("*.md")) + sorted((ROOT / "opencode" / "agents").glob("*.md"))
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            for part in ("last message is this report alone", "no running commentary",
                         "never list what passed", "With nothing to report", "never end without it"):
                self.assertIn(part, text, path.name)

    def test_agent_budget_is_600(self):
        self.assertEqual(measure().LIMITS["agent"], 600)


if __name__ == "__main__":
    unittest.main()
