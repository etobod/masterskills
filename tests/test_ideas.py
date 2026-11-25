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
            "skills/loc-planning/SKILL.md": 2950,
            "skills/loc-review/SKILL.md": 950, "skills/loc-diagram/SKILL.md": 850, "skills/loc-qa/SKILL.md": 1050,
            "skills/loc-director/SKILL.md": 850, "skills/loc-init/SKILL.md": 850,
            "skills/loc-orchestrate/references/design.md": 850, "skills/loc-orchestrate/references/gates.md": 950,
            "skills/loc-orchestrate/references/stuck.md": 900, "skills/loc-orchestrate/references/run.md": 1400,
            "skills/loc-orchestrate/references/divergent.md": 850,
            "skills/loc-orchestrate/references/search.md": 900, "skills/loc-planning/references/prd.md": 850,
            "agents/architect.md": 700, "agents/design-critic.md": 800, "agents/designer.md": 650,
            "agents/rubber-duck.md": 720, "agents/judge.md": 750,
        }
        self.assertEqual(overrides, expected)
        self.assertEqual(measure().LIMITS["rule"], 595)


class DivergentCriticTest(unittest.TestCase):
    """plan 86, B-03: the critic judges divergent variants; it never picks."""

    def test_the_critic_has_a_divergent_mode(self):
        text = read("agents/design-critic.md")
        section = re.search(r"## Divergent\n(.*?)\n## ", text, re.S).group(1)
        for phrase in ("fit another project", "make it first", "names a fact from `**Facts:**`",
                       "known opposite", "`loc/moves.md`", "working parts are whole", "never pick"):
            self.assertIn(phrase, section)
        self.assertIn("`<name>: pass` or `<name>: fail`", text)
        self.assertIn("light, full or divergent", text)
        # a divergent report lists every pass; the "never list what passed" rule is for light and full
        self.assertIn("outside `divergent`, never list what passed", text)

    def test_the_designer_sketches_variants_then_builds_the_pick(self):
        text = read("agents/designer.md")
        self.assertIn("as a sketch", text)
        self.assertIn("only the picked one in full", text)


class DivergentFlowTest(unittest.TestCase):
    """plan 86, B-02 and B-05: where a divergent milestone comes from and how it runs."""

    def test_planning_marks_creative_results_divergent(self):
        text = read("skills/loc-planning/SKILL.md")
        for phrase in ("**divergent** (`**Kind:** divergent`)", "a name, a text, a visual direction or a concept",
                       "never for identifiers in code", "references/divergent.md"):
            self.assertIn(phrase, text)

    def test_run_routes_divergent_milestones(self):
        text = read("skills/loc-orchestrate/references/run.md")
        self.assertIn("`**Kind:** divergent` follows `references/divergent.md`", text)
        self.assertIn("`waiting: user pick` is done, never stuck", text)

    def test_the_flow_has_its_six_steps_and_never_waits(self):
        text = read("skills/loc-orchestrate/references/divergent.md")
        for step in ("1. **Default.**", "2. **Start.**", "3. **Variants.**", "4. **Critic.**", "5. **Pick.**",
                     "6. **Build.**"):
            self.assertIn(step, text)
        for phrase in ("seed.py visual|text|idea", "moves.py show --last 12", "`design-critic` agent in `divergent` mode",
                       "--by interim", "the plan never waits for the pick", "added to `questions`",
                       "moves.py add", "At most one is the **safe** variant", "reworked once"):
            self.assertIn(phrase, text)
        answer = text.split("## The user's answer", 1)[1]
        self.assertIn("--by user", answer)
        self.assertIn("**None of them** (`--name none`): a `deferred` file asks for new variants once", answer)
        self.assertIn("a second `None of them` becomes a `question` file", answer)

    def test_the_skill_records_the_users_pick(self):
        self.assertIn("a divergent pick also with `divergent_log.py --pick --by user`",
                      read("skills/loc-orchestrate/SKILL.md"))


class LadderTest(unittest.TestCase):
    def implement_step(self) -> str:
        text = read("skills/loc-orchestrate/references/run.md")
        return re.search(r"2\. \*\*Implement\*\*.*?\n3\. ", text, re.S).group(0)

    def test_orchestrate_climbs_the_ladder_before_code(self):
        step = self.implement_step()
        for rung in ("already in the project", "standard library", "platform",
                     "installed dependency", "one line"):
            self.assertIn(rung, step)
        for kept in ("validation", "error handling", "security", "accessibility"):
            self.assertIn(kept, step)

    def test_the_orchestrator_builds_and_climbs_the_ladder_itself(self):
        # The main session carried the plan's whole work (B-02): the orchestrator agent builds it.
        self.assertIn("exactly this milestone yourself", self.implement_step())

    def test_code_review_flags_code_that_already_exists(self):
        self.assertNotIn('Skill(skill: "code-review"', read("skills/loc-orchestrate/SKILL.md"))  # once per plan
        for rel in ("skills/loc-review/SKILL.md",):
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
        for text in (review,):
            self.assertIn("once per round", text)
            self.assertIn("never a relaunch", text)

    def test_an_empty_agent_answer_is_a_lost_report(self):
        gate = self.read("skills/loc-planning/SKILL.md").split("## 6. Gate", 1)[1].split("\n## ", 1)[0]
        review = self.read("skills/loc-review/SKILL.md").split("## 2. Review, in parallel", 1)[1].split("\n## ", 1)[0]
        for text in (gate, review):
            self.assertIn("lost agent report is asked for again (core rule 6a)", text)
        rule = read("rules/core.md").split("6a. ", 1)[1].split("\n7. ", 1)[0]
        for part in ("`Findings: <n>`", "`End of report.`", "empty answer", "no end line",
                     "fewer findings than announced", "`judge`", "never clean",
                     "same agent again, up to 3 times", "never a relaunch", "still lost fails the round"):
            self.assertIn(part, rule)

    def test_the_plan_is_reviewed_once_with_its_whole_diff(self):
        # poe: 419 code-review runs, mostly one per milestone (B-01).
        review = self.read("skills/loc-review/SKILL.md").split("## 2. Review, in parallel", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Orchestrated, the whole plan's diff: no milestone was reviewed before.", review)
        steps = self.read("skills/loc-orchestrate/references/run.md").split("## 2. Each milestone", 1)[1].split("\n## ", 1)[0]
        self.assertNotIn("Code-review gate", steps)
        self.assertIn("No review here: the plan is reviewed once, at the end.", steps)
        self.assertNotIn("M<n>/code-review", self.read("skills/loc-orchestrate/references/search.md"))


    def test_only_blocking_findings_start_a_fix_round(self):
        # poe: about 240 fix rounds and 345 judge calls (B-22).
        gates = self.read("skills/loc-orchestrate/references/gates.md")
        for part in ("a wrong result", "data lost or distorted", "a crash or a hang", "a failing proof or test",
                     "a broken `## Invariants` entry", "Nothing else is blocking.",
                     "Only a round with Blocking findings calls the `judge`", '"is it really blocking?"',
                     "Non-blocking findings never go to the judge", "- non-blocking (final-review):",
                     "### Repeated non-blocking findings", "## Rounds 2 and 3"):
            self.assertIn(part, gates)
        review = self.read("skills/loc-review/SKILL.md").split("## 4. Orchestrated mode", 1)[1].split("\n## ", 1)[0]
        for part in ("Only Blocking findings", '"is it really blocking?"', "Rounds 2 and 3 review only the fixes' diff",
                     "get no judge and no fix", "a repeat of an earlier plan's non-blocking line"):
            self.assertIn(part, review)
        judge = self.read("agents/judge.md")
        self.assertIn("A review gate gives you only Blocking findings", judge)
        self.assertIn("**is it really blocking?**", judge)

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

    def test_a_plan_that_is_not_ready_goes_to_planning_without_the_architect(self):
        # A run asked the architect (Decide), which rewrote the proofs in place and used up the last gate round.
        self.assertIn("point to `/masterskills:loc-planning`; no architect, no edits to the plan.",
                      read("skills/loc-orchestrate/SKILL.md"))

    def test_proofs_are_single_commands(self):
        planning = read("skills/loc-planning/SKILL.md")
        self.assertIn("one command each (never chained: `;`, `&&`, `if ($?)`)", planning)
        self.assertNotIn("exactly one `**Proof:**` line", planning)
        self.assertIn("run each `Proof` line exactly as written, one at a time", read("skills/loc-orchestrate/references/run.md"))
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
        self.assertIn("references/search.md", read("skills/loc-orchestrate/references/run.md"))
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


class ProjectFrameTest(unittest.TestCase):
    """No goal, no work: the skills that start work check the frame and ask in the main session."""

    def test_skills_check_the_frame_before_their_work(self):
        for skill in ("loc-planning", "loc-orchestrate", "loc-director"):
            with self.subTest(skill=skill):
                text = read(f"skills/{skill}/SKILL.md")
                self.assertIn("scripts/frame.py", text)
                self.assertIn("skills/loc-init/references/frame.md", text)

    def test_frame_reference_asks_three_ways(self):
        text = read("skills/loc-init/references/frame.md")
        for part in ("AskUserQuestion", "**Accept**", "**Correct in my words**", "**Reject**", "Test command",
                     "next_number.py --type brainstorm"):
            self.assertIn(part, text)

    def test_loc_init_takes_a_description_in_one_pass(self):
        init = read("skills/loc-init/SKILL.md")
        self.assertIn("any other text → a **description**", init)
        self.assertIn('"From a description"', init)
        self.assertIn("After their first answer, draft the frame", init)
        self.assertIn("nothing they wrote may be lost", read("skills/loc-init/references/frame.md"))
        brainstorm = read("skills/loc-brainstorm/SKILL.md")
        self.assertIn("skills/loc-init/references/frame.md", brainstorm)
        self.assertNotIn("Fill the project from", brainstorm)

    def test_rule_nine_asks_for_an_empty_frame(self):
        self.assertIn("an empty one is filled by asking", read("rules/core.md"))


class StuckLadderTest(unittest.TestCase):
    """poe: 28 architect calls, no question to the user after day one, stuck 017 -> plan 024 -> stuck 021."""

    def test_one_replan_per_stuck_file_then_only_ask(self):
        triage = read("agents/architect.md").split("## Triage", 1)[1].split("## Report", 1)[0]
        self.assertIn("A plan made from a stuck file that got stuck again: only **ask**", triage)
        stuck = read("skills/loc-orchestrate/references/stuck.md")
        self.assertIn("A plan whose `**Source:**` is a stuck file gets only **ask**", stuck)
        self.assertIn("after Triage (now only **ask**) the new plan", stuck)
        self.assertIn("a `stuck` also gets `**Replanned:** <plan NNN>`", read("skills/loc-planning/SKILL.md"))

    def test_architect_escalates_by_a_checkable_list(self):
        competence = read("agents/architect.md").split("## Competence", 1)[1].split("## Decide", 1)[0]
        for point in ("changes what the user sees or reads", "changes what counts as correct data",
                      "closes or drops work", "is empty", "When unsure, escalate", "name the point"):
            self.assertIn(point, competence)
        self.assertEqual(len(re.findall(r"(?m)^\d\. ", competence)), 5)

    def test_questions_of_a_plan_come_together(self):
        self.assertIn("a plan keeps one, a `###` per matter, asked together at its end", read("rules/core.md"))
        self.assertIn("asks them all in one round when the plan ends", read("skills/loc-orchestrate/references/stuck.md"))
        self.assertIn("every matter in one `AskUserQuestion` round", read("skills/loc-orchestrate/SKILL.md"))
        self.assertIn("`Plan <NNN>: questions`", read("templates/loc/inbox/question.md"))


if __name__ == "__main__":
    unittest.main()
