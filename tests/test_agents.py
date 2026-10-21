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
        self.assertIn("## Final review triage", stuck)
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
        self.assertIn('--source "<gate, e.g. M1 code-review (milestone)> of <plan path>"', stuck)
        for marker in ("**Stuck gates:**", "**Architect (Challenge):**", "**Architect (Triage):**", "**Next:**"):
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
