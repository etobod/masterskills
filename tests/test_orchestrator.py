"""The orchestrator agent runs a plan; the main session only starts it and asks its questions (B-02, B-23).

poe: the main session used 61% of the tokens, about 135k of context per call and 179 compactions.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scripts import ROOT, scratch_dir  # noqa: E402


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def tools(text: str) -> set:
    line = re.search(r"^tools:(.*)$", text, re.MULTILINE)
    return {tool.strip() for tool in line.group(1).split(",")} if line else set()


class OrchestratorAgentTest(unittest.TestCase):
    def test_the_agent_reads_the_procedure_and_never_asks(self):
        agent = read("agents/orchestrator.md")
        self.assertIn("Agent", tools(agent))
        self.assertIn("TaskStop", tools(agent))  # rule 7 stops background commands
        self.assertIn("Skill", tools(agent))
        for part in ("**Plan**", "**State**", "**Procedure**: `run.md`. Read it first",
                     "You implement every milestone yourself", "**Never ask the user.**",
                     "`questions` in the state file", "`Status: waiting: questions`", "End of report.",
                     "Write it out in every command", "`rules/core.md`", "**No forgotten shells.**",
                     "follow **Long commands** in `run.md`", "only with a deadline", "stopped (`TaskStop`)"):
            self.assertIn(part, agent)
        for worker in ("test-author", "designer", "design-critic", "searcher", "researcher", "rubber-duck", "judge", "architect"):
            self.assertIn(f"`{worker}`", agent)

    def test_redundant_tests_are_removed_by_the_plugin(self):
        # A suite grew to three times the code: tests were only ever added, never removed.
        duck = read("agents/rubber-duck.md")
        self.assertIn("a new test that repeats what an existing test or layer checks, or checks the exact wording "
                      "of text the user reads, Non-blocking, fixed by removing it", duck)
        self.assertIn("A test a review finding removes (a duplicate, a wording check) goes the same way",
                      read("skills/loc-orchestrate/references/tests.md"))
        review = read("skills/loc-review/SKILL.md")
        for part in ("- **`tests`** → standalone, scope `Whole test suite` below, without asking.",
                     "start its own browser or page load", "suite_size.py --reviewed",
                     "called as `tests`, ask nothing: one review per top-level test directory"):
            self.assertIn(part, review)
        qa = read("skills/loc-qa/SKILL.md")
        self.assertIn("suite_size.py --record <NNN or ->", qa)
        self.assertIn("`due: true` → row **INFO** `suite review due`", qa)
        self.assertIn('when QA reported `suite review due`, `Skill(skill: "masterskills:loc-review", args: "tests")`',
                      read("skills/loc-orchestrate/references/run.md"))
        template = read("templates/loc/TEST-PLAN.md")
        self.assertIn("is removed, not extended", template)
        self.assertIn("one browser per run, each page loaded once per width", template)

    def test_a_milestone_runs_only_its_proof(self):
        # Layers after every milestone ran a whole suite each time: minutes per milestone.
        tests = read("skills/loc-orchestrate/references/tests.md")
        self.assertIn("No layer of `loc/TEST-PLAN.md` section (a) runs after a milestone", tests)
        self.assertNotIn("fast layers", tests + read("skills/loc-planning/SKILL.md"))
        self.assertNotIn("after every", read("templates/loc/TEST-PLAN.md"))
        # The one exception, the same in both: a UI milestone checks its own pages.
        self.assertIn("except `ui_check.py` on a UI milestone's own pages", tests)
        self.assertIn("A UI milestone adds `ui_check.py` on its own pages", read("skills/loc-planning/SKILL.md"))

    def test_a_proof_runs_in_the_foreground(self):
        # A proof sent to the background and polled forever kept shells running into the final review.
        run = read("skills/loc-orchestrate/references/run.md")
        for part in ("**Long commands.**", "in any step or reference (search, divergent, a rerun after a fix, QA)",
                     "timeout at its maximum, `600000` ms", "never start one while another still runs",
                     "A foreground run the timeout kills is no failure", "never with `&` or a detached start",
                     "No fourth round or code change: stop your background commands", "killed included, never an endless `until` loop",
                     "count the round as failed, cause `exceeds the time limit`, never a code fix",
                     "Before a milestone becomes `done` or `stuck`, before the QA gate, the final review and every stop or report",
                     "Run it as **Long commands** above says.", "7. Stop your background commands (**Long commands**)"):
            self.assertIn(part, run)

    def test_only_the_orchestrator_starts_agents(self):
        # Two levels: the orchestrator and its workers; a worker never starts another agent.
        for path in sorted((ROOT / "agents").glob("*.md")):
            if path.name != "orchestrator.md":
                self.assertFalse(tools(path.read_text(encoding="utf-8")) & {"Agent", "Task"}, path.name)

    def test_nothing_the_agent_reads_asks_the_user(self):
        # The agent has no question tool: a reference that says AskUserQuestion leaves it with no path.
        for path in sorted((ROOT / "skills" / "loc-orchestrate" / "references").glob("*.md")):
            self.assertNotIn("AskUserQuestion", path.read_text(encoding="utf-8"), path.name)

    def test_run_md_holds_the_milestone_and_the_end(self):
        run = read("skills/loc-orchestrate/references/run.md")
        for part in ("## 2. Each milestone", "**Snapshot** `--point start`", "**Implement**", "**Proof gate**",
                     "**Manual check**", "## 3. Deviations from the plan", "## 5. At the end", "**QA gate**",
                     'Skill(skill: "masterskills:loc-review", args: "plan <NNN>")', "**Journal.**", "**Commit**",
                     "Status: done | waiting: questions | stopped: permissions"):
            self.assertIn(part, run)
        self.assertNotIn("*inline*", run)
        self.assertNotIn("*subagent*", run)

    def test_the_skill_only_starts_and_asks(self):
        skill = read("skills/loc-orchestrate/SKILL.md")
        self.assertIn('Agent(subagent_type: "masterskills:orchestrator"', skill)
        self.assertIn("Procedure: ${CLAUDE_PLUGIN_ROOT}/skills/loc-orchestrate/references/run.md", skill)
        for part in ("scripts/frame.py", "check_plan.py --ready", "test_baseline.py", '"mode": "agent"',
                     "every matter in one `AskUserQuestion` round", "set `questions` to `[]`",
                     "asked for again from the same agent", "never start a second orchestrator",
                     "`phase` `done`: the plan is finished", "the plan is done, so never back to §2"):
            self.assertIn(part, skill)
        for moved in ("**Proof gate**", "commit_plan.py", "memory_index.py"):
            self.assertNotIn(moved, skill)
        # No compaction rule: the agent keeps the main session small (B-04).
        self.assertNotIn("compact", skill.lower())


class QuestionsInStateTest(unittest.TestCase):
    def check(self, questions) -> list:
        project = scratch_dir(self)
        state = {"plan": "loc/inbox/007-plan-x.md", "mode": "agent", "milestone": 1, "phase": "implement",
                 "milestones": [{"id": "M1", "status": "in_progress", "start": None, "end": None}],
                 "gates": {}, "deviations": [], "next_action": "x", "updated": "2026-11-25 10:00",
                 "questions": questions}
        path = project / "loc" / "state" / "007.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(state), encoding="utf-8")
        out = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "check_state.py"), str(path)],
                             capture_output=True, text=True, cwd=project)
        return json.loads(out.stdout)["problems"]

    def test_a_question_file_or_the_sheet(self):
        self.assertEqual(self.check([{"file": "loc/inbox/009-U-question-plan-007.md", "ask": "Which store?"},
                                     {"file": "loc/inbox/008-U-checks.html", "ask": "Rate M2"}]), [])

    def test_null_is_no_questions(self):
        self.assertEqual(self.check(None), [])

    def test_anything_else_is_a_problem(self):
        for bad in ([{"file": "loc/inbox/009-deferred-x.md", "ask": "x"}],
                    [{"file": "loc/inbox/009-U-question-x.md", "ask": ""}],
                    [{"file": "loc/inbox/009-U-question-x.md"}], "x"):
            problems = self.check(bad)
            self.assertTrue(any(p.startswith("questions:") for p in problems), (bad, problems))


if __name__ == "__main__":
    unittest.main()
