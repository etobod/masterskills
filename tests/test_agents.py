"""The project's recorded decisions: the architect agent, the judge and the skills that call them."""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def front(text: str) -> str:
    return re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)


class DecisionAgentsTest(unittest.TestCase):
    def test_architect_reads_only_and_has_both_modes(self):
        text = read("agents/architect.md")
        head = front(text)
        self.assertIn("name: architect", head)
        self.assertRegex(head, r"(?m)^tools: Read, Grep, Glob$")
        for marker in ("## Decisions", "Harvest", "Challenge", "replaces D-", "recommended"):
            self.assertIn(marker, text)

    def test_opencode_builds_architect_as_read_only_subagent(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        result = subprocess.run([sys.executable, "-B", str(ROOT / "opencode" / "build.py"), "--out", str(out)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        head = front((out / "agents" / "architect.md").read_text(encoding="utf-8"))
        self.assertIn("mode: subagent", head)
        self.assertIn("edit: deny", head)

    def test_judge_weighs_decisions(self):
        text = read("agents/judge.md")
        self.assertIn("`## Decisions`", text)
        self.assertIn("challenges D-", text)
        self.assertIn("[D-", text)


class DecisionSkillsTest(unittest.TestCase):
    def test_orchestrate_calls_the_architect(self):
        self.assertIn("challenges D-", read("skills/loc-orchestrate/references/gates.md"))
        self.assertIn("`architect`", read("skills/loc-orchestrate/references/gates.md"))
        self.assertIn("`architect`", read("skills/loc-orchestrate/references/stuck.md"))

    def test_planning_cites_and_records_decisions(self):
        skill = read("skills/loc-planning/SKILL.md")
        self.assertIn("D-01", skill)
        self.assertRegex(skill, r"rubber-duck.*D-")
        prd = read("skills/loc-planning/references/prd.md")
        self.assertIn("## Decisions", prd)
        self.assertIn("replaces D-", prd)

    def test_planning_asks_about_proposed_decisions(self):
        decisions = read("skills/loc-planning/references/prd.md").split("## `Decisions`")[1]
        self.assertIn('--type question --slug "decisions"', decisions)
        self.assertIn("After the answer: write the approved lines to loc/PRD.md ## Decisions.", decisions)

    def test_final_review_goes_to_triage(self):
        architect = read("agents/architect.md")
        self.assertIn("## Triage", architect)
        for verdict in ("**retry**", "**plan**", "**ask**"):
            self.assertIn(verdict, architect)
        stuck = read("skills/loc-orchestrate/references/stuck.md")
        self.assertIn("## Triage", stuck)
        self.assertIn("--type deferred", stuck)
        self.assertIn("--type question", stuck)
        self.assertIn("`triage`", read("skills/loc-orchestrate/SKILL.md"))
        self.assertIn("`retry`", read("skills/loc-review/SKILL.md"))

    def test_every_inbox_file_names_its_author(self):
        found = 0
        for path in [*ROOT.glob("skills/**/*.md"), *ROOT.glob("agents/*.md"), *ROOT.glob("rules/*.md"),
                     *ROOT.glob("hooks/*.py")]:
            lines = path.read_text(encoding="utf-8").splitlines()
            for number, line in enumerate(lines):
                if re.search(r"next_number\.py\S*\s.*--type |--type <question", line):
                    found += 1
                    # A command in Python source may continue on the next line.
                    self.assertIn("--by", "\n".join(lines[number:number + 2]), f"{path.relative_to(ROOT)}: {line[:80]}")
        self.assertGreaterEqual(found, 16)

    def test_stuck_records_the_verdict_on_top(self):
        stuck = read("skills/loc-orchestrate/references/stuck.md")
        self.assertIn('--source "<gate, e.g. final-review> of <plan path>"', stuck)
        for marker in ("**Stuck gates:**", "**Architect (Triage):**", "**Next:**"):
            self.assertIn(marker, stuck)

    def test_questions_outside_a_skill_and_new_directories(self):
        rules = read("rules/core.md")
        self.assertIn("in a skill or not", rules)
        self.assertNotIn("the user tracks their own questions", rules)
        orchestrate = read("skills/loc-orchestrate/SKILL.md")
        for marker in ("--add <dir>", "--leave <dir>", ".gitignore"):
            self.assertIn(marker, orchestrate)

    def test_init_harvests_after_migration(self):
        skill = read("skills/loc-init/SKILL.md")
        self.assertIn("harvest", skill)
        self.assertIn("`architect`", skill)


class OptionLabelTest(unittest.TestCase):
    def test_rule_names_options_and_accepts_delegated_answers(self):
        rule = read("rules/core.md").split("8. ")[1].split("\n9. ")[0]
        self.assertIn("as the architect recommends", rule)
        self.assertIn("088 A:", rule)

    def test_architect_names_options_by_verb(self):
        report = read("agents/architect.md").split("## Report")[1]
        self.assertNotRegex(report, r"(?m)^\d\. ")
        self.assertIn("Bears on:", report)

    def test_question_template_letters_only_options(self):
        template = read("templates/loc/inbox/question.md")
        self.assertIn("not lettered", template)


class ArchitectFirstTest(unittest.TestCase):
    def test_architect_decides_within_its_competence(self):
        text = read("agents/architect.md")
        for marker in ("## Competence", "## Priorities", "## Decide", "**decide**", "**escalate**",
                       "cost if wrong", "(architect, <date>)"):
            self.assertIn(marker, text)

    def test_only_an_escalation_asks_the_user(self):
        found = 0
        for path in [*ROOT.glob("skills/**/*.md"), *ROOT.glob("agents/*.md"), *ROOT.glob("rules/*.md")]:
            if path.name == "prd.md":  # a change to Goal, Core idea or Scenarios is always the user's
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if "--type question" in line:
                    found += 1
                    self.assertIn('--by "architect (', line, f"{path.relative_to(ROOT)}: {line[:80]}")
        self.assertGreaterEqual(found, 4)

    def test_skills_call_the_architect_before_a_question(self):
        planning = read("skills/loc-planning/SKILL.md").split("## 4.")[1].split("## 5.")[0]
        self.assertIn("Decide", planning)
        orchestrate = read("skills/loc-orchestrate/SKILL.md")
        rule4 = orchestrate.split("**Rule 4**")[1].splitlines()[0]
        self.assertIn("Decide", rule4)

    def test_brainstorm_is_open_until_approved(self):
        self.assertIn("**Status:** open", read("templates/loc/inbox/brainstorm.md"))
        skill = read("skills/loc-brainstorm/SKILL.md")
        for marker in ("approved <date>", "inbox_owner.py --number", "--director"):
            self.assertIn(marker, skill)


class StuckInPlanTest(unittest.TestCase):
    def test_milestone_and_qa_record_in_the_plan(self):
        stuck = read("skills/loc-orchestrate/references/stuck.md")
        milestone = stuck.split("## Stuck milestone or QA gate")[1].split("\n## ")[0]
        for marker in ("## Stuck gates", "**Remains:**", "**Continued with:**", '`"plan"`'):
            self.assertIn(marker, milestone)
        self.assertNotIn("next_number.py", milestone)
        self.assertNotIn("Challenge", milestone)
        triage = stuck.split("## Triage")[1]
        self.assertIn("even though the final review passed", triage)
        orchestrate = read("skills/loc-orchestrate/SKILL.md")
        self.assertIn("## Stuck gates", orchestrate)
        self.assertNotIn("single `stuck` file", orchestrate)
        template = read("templates/loc/inbox/stuck.md")
        self.assertNotIn("Challenge", template)

    def test_triage_asks_only_beyond_competence(self):
        triage = read("agents/architect.md").split("## Triage")[1].split("## Report")[0]
        self.assertIn("in circles", triage.split("**plan**")[1].split("**ask**")[0])
        self.assertIn("beyond your competence", triage.split("**ask**")[1])


class PlanGateTriageTest(unittest.TestCase):
    def test_failed_plan_gate_goes_to_triage(self):
        planning = read("skills/loc-planning/SKILL.md").split("## 6.")[1].split("## 7.")[0]
        for marker in ("`architect`", "Triage", "## Plan gate"):
            self.assertIn(marker, planning)
        gate = read("skills/loc-orchestrate/references/stuck.md").split("## Plan gate")[1].split("\n## ")[0]
        for verdict in ("**retry**", "**plan**", "**ask**", "open — gate failed", "--type question"):
            self.assertIn(verdict, gate)

    def test_review_file_waits_for_the_director(self):
        standalone = read("skills/loc-review/SKILL.md").split("## 5.")[1].split("## 6.")[0]
        self.assertNotIn("the user decides", standalone)
        for marker in ("`judge`", "no `U`", "escalat"):
            self.assertIn(marker, standalone)

    def test_pm_orders_inbox_work_with_plans(self):
        pm = read("agents/pm.md")
        for marker in ("`deferred`", "`stuck`", "`review`", "`U`"):
            self.assertIn(marker, pm)


class PmTest(unittest.TestCase):
    def test_pm_reads_only_and_orders_the_queue(self):
        text = read("agents/pm.md")
        head = front(text)
        self.assertIn("name: pm", head)
        self.assertRegex(head, r"(?m)^tools: Read, Grep, Glob$")
        for marker in ("## Priorities", "## Goal", "plan_queue.py --set", "urgent", "running"):
            self.assertIn(marker, text)

    def test_opencode_builds_pm_as_read_only_subagent(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        result = subprocess.run([sys.executable, "-B", str(ROOT / "opencode" / "build.py"), "--out", str(out)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        head = front((out / "agents" / "pm.md").read_text(encoding="utf-8"))
        self.assertIn("mode: subagent", head)
        self.assertIn("edit: deny", head)

    def test_skills_call_the_pm(self):
        planning = read("skills/loc-planning/SKILL.md")
        self.assertIn("`pm`", planning)
        self.assertIn("--set", planning)
        init = read("skills/loc-init/SKILL.md")
        for marker in ("`pm`", "regroup", "deferred", "--set"):
            self.assertIn(marker, init)


if __name__ == "__main__":
    unittest.main()
