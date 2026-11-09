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
    def test_judge_fixes_visible_defects(self):
        # A judge passed unstyled buttons beside styled chips as "enough": still clickable.
        judge = (ROOT / "agents" / "judge.md").read_text(encoding="utf-8")
        self.assertIn("A visible defect on a screen the plan changes", judge)
        self.assertIn('"it still works" is no reason for `enough`', judge)

    def test_raised_limits(self):
        overrides = measure().OVERRIDES
        expected = {
            "skills/loc-orchestrate/SKILL.md": 1400, "skills/loc-planning/SKILL.md": 2770,
            "skills/loc-review/SKILL.md": 950, "skills/loc-diagram/SKILL.md": 850, "skills/loc-qa/SKILL.md": 1050,
            "skills/loc-director/SKILL.md": 850, "skills/loc-init/SKILL.md": 850,
            "skills/loc-orchestrate/references/design.md": 850, "skills/loc-orchestrate/references/gates.md": 850,
            "skills/loc-orchestrate/references/stuck.md": 850,
            "skills/loc-orchestrate/references/search.md": 900, "skills/loc-planning/references/prd.md": 850,
            "agents/architect.md": 650, "agents/design-critic.md": 650, "agents/designer.md": 650,
            "agents/rubber-duck.md": 720, "agents/judge.md": 750,
        }
        self.assertEqual(overrides, expected)
        self.assertEqual(measure().LIMITS["rule"], 595)


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

    def test_the_file_is_english_the_answer_in_the_users_language(self):
        # Core rule 1: English in `loc/`; the walk-through was written there in the user's language.
        text = read("skills/loc-diagram/SKILL.md")
        self.assertIn("Under the diagram, in English", text)
        self.assertNotIn("Under the diagram, in the user's language", text)
        self.assertIn("those three in the user's language", text)


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

    def test_an_empty_agent_answer_is_a_lost_report(self):
        gate = self.read("skills/loc-planning/SKILL.md").split("## 6. Gate", 1)[1].split("\n## ", 1)[0]
        review = self.read("skills/loc-review/SKILL.md").split("## 2. Review, in parallel", 1)[1].split("\n## ", 1)[0]
        step5 = [line for line in self.read("skills/loc-orchestrate/SKILL.md").splitlines()
                 if line.startswith("5. **Code-review gate**")][0]
        for text in (gate, review, step5):
            self.assertIn("lost agent report is asked for again (core rule 6a)", text)
        rule = read("rules/core.md").split("6a. ", 1)[1].split("\n7. ", 1)[0]
        for part in ("`Findings: <n>`", "`End of report.`", "empty answer", "no end line",
                     "fewer findings than announced", "`judge`", "never clean",
                     "same agent again, up to 3 times", "never a relaunch", "still lost fails the round"):
            self.assertIn(part, rule)

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
                         "never list what passed", "With nothing to report", "never end without it",
                         "Its last line is `End of report.`"):
                self.assertIn(part, text, path.name)

    def test_reviewers_announce_how_many_findings(self):
        for rel in ("agents/rubber-duck.md", "agents/judge.md", "agents/design-critic.md", "opencode/agents/code-review.md"):
            self.assertIn("Its first line is `Findings: <n>`, how many it lists.", read(rel), rel)

    def test_the_caller_never_restates_an_agents_rules(self):
        # A caller's own summary ("pick at most 10") contradicted the agent's definition.
        rule = read("rules/core.md").split("6b. ", 1)[1].split("\n7. ", 1)[0]
        for part in ("only what the skill says to give it", "each part labelled", "a file by its path, never copied", "never a role",
                     "a summary of its rules", "a limit or an output format of your own", "its definition has them"):
            self.assertIn(part, rule)

    def test_agent_budget_is_600(self):
        self.assertEqual(measure().LIMITS["agent"], 600)


class PlanGateLoopTest(unittest.TestCase):
    """A base plan was planned three times (stuck, plan, stuck…) and nothing ran: the proofs could not be written."""

    def test_a_failed_plan_from_a_stuck_plan_gate_merges_into_it(self):
        # Each failed replan made a new stuck file and left the plans before it open.
        gate = read("skills/loc-orchestrate/references/stuck.md").split("## Plan gate", 1)[1].split("\n## ", 1)[0]
        self.assertIn("makes no stuck file of its own", gate)
        self.assertIn("`**Status:** closed — replaced by <new plan>`", gate)
        self.assertIn("`**Status:** closed — merged into <stuck file>`", gate)
        self.assertIn("the stuck file stays open", gate)
        self.assertNotIn("**Ruling:**", gate)
        self.assertNotIn("stuck plan gate", read("agents/architect.md"))
        self.assertIn("except a stuck `## plan gate` (`stuck.md`)", read("skills/loc-planning/SKILL.md"))

    def test_proofs_are_single_commands(self):
        planning = read("skills/loc-planning/SKILL.md")
        self.assertIn("one command each (never chained: `;`, `&&`, `if ($?)`)", planning)
        self.assertNotIn("exactly one `**Proof:**` line", planning)
        self.assertIn("run each `Proof` line exactly as written, one at a time", read("skills/loc-orchestrate/SKILL.md"))
        self.assertIn("One command per `**Proof:**` line", read("templates/loc/inbox/plan.md"))

    def test_documents_are_proved_by_their_sections(self):
        planning = read("skills/loc-planning/SKILL.md")
        self.assertIn("never a checking script it writes", planning)
        self.assertIn("A document goes into the milestone whose work it describes", planning)
        duck = read("agents/rubber-duck.md")
        self.assertIn("proofs that each document has its sections are enough", duck)
        self.assertIn("`${CLAUDE_PLUGIN_ROOT}` in a plan is filled in by whoever runs it, never a finding", duck)

    def test_a_dev_server_is_started_by_the_proof(self):
        self.assertIn("a dev server started by its `--serve`", read("skills/loc-planning/SKILL.md"))
        self.assertIn('`--serve "<its start command>"`', read("skills/loc-orchestrate/references/design.md"))


class SearchMilestoneTest(unittest.TestCase):
    """A search milestone improves a number toward a target; missing it is accepted, never stuck."""

    def test_skills_point_to_the_search_reference(self):
        reference = read("skills/loc-orchestrate/references/search.md")
        for part in ("**Kind:** search", "search_log.py --start", "search_log.py --add", "--metric-change",
                     "`searcher`", "`judge`", "Could go further", "`deferred`", "never stuck"):
            self.assertIn(part, reference)
        self.assertIn("references/search.md", read("skills/loc-orchestrate/SKILL.md"))
        planning = read("skills/loc-planning/SKILL.md")
        self.assertIn("references/search.md", planning)
        self.assertIn("never a way out of a hard proof", planning)
        self.assertIn("whether a measurement is needed at all", planning)

    def test_measuring_stays_in_proportion(self):
        reference = read("skills/loc-orchestrate/references/search.md")
        for part in ("Is the number already known?", "**Baseline:**", "**Quick metric:**", "--confirm",
                     "nothing is measured before the first try", "Measuring grows with progress", "time spent measuring is never a reason",
                     "**Quick target:**", "--quick-target", "`git show <start>:<file>`", "never `git checkout`"):
            self.assertIn(part, reference)
        self.assertIn("measuring out of proportion", read("agents/rubber-duck.md"))
        self.assertIn("not one quick run at the start", read("agents/rubber-duck.md"))
        self.assertIn("**Kind:** search", read("templates/loc/inbox/plan.md"))

    def test_declined_screenshots_leave_only_the_tokens_check(self):
        # Without a browser, a proof with `--check` or `--out` exits 2 on every UI milestone.
        self.assertIn("(with `Screenshots: declined`, `--tokens` only;", read("skills/loc-planning/SKILL.md"))
        plan = read("templates/loc/TEST-PLAN.md")
        self.assertIn("(only this one with `Screenshots: declined`)", plan)
        self.assertIn("none with `Screenshots: declined`", plan)
        self.assertIn("None with `Screenshots: declined`.", read("skills/loc-orchestrate/references/design.md"))

    def test_kind_is_proof_or_search_never_traditional(self):
        for rel in ("skills/loc-orchestrate/references/search.md", "skills/loc-planning/SKILL.md",
                    "agents/searcher.md", "agents/rubber-duck.md"):
            self.assertNotIn("traditional", read(rel).lower(), rel)

    def test_agents_know_the_search(self):
        searcher = read("agents/searcher.md")
        self.assertIn("tools: Read, Grep, Glob, Edit, Write", front(searcher))
        self.assertIn("Never touch the metric", searcher)
        self.assertIn("never whether it reaches the target", read("agents/rubber-duck.md"))
        self.assertIn("metric, cases, hold-out or guard", read("agents/judge.md"))


if __name__ == "__main__":
    unittest.main()
