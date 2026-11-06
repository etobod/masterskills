"""A project with a user interface: the `## Frontend` section, the UI proof in plans,
the visual direction in brainstorms and the design review."""

import json
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


def section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


class FrontendSectionTest(unittest.TestCase):
    def test_template_describes_the_section(self):
        body = section(read("templates/CLAUDE.md"), "## Frontend")
        for part in ("user interface", "empty", "design plugin", "review", "UI check",
                     "screenshot", "widths"):
            self.assertIn(part, body)

    def test_init_adds_the_section_to_an_existing_claude_md(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        (project / "CLAUDE.md").write_text("## Commands\n`make test`\n", encoding="utf-8")
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "init_project.py"), "--project", "."],
                             cwd=project, capture_output=True, text=True, encoding="utf-8")
        report = json.loads(out.stdout)
        added = [u for u in report["updated"] if u["path"] == "CLAUDE.md"][0]["added"]
        self.assertIn("Frontend", added)
        self.assertIn("## Frontend", (project / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_brainstorm_mapping_names_the_section(self):
        table = read("skills/loc-init/references/brainstorm.md")
        self.assertRegex(table, r"\| a user interface[^|]*\| `Frontend` \|")

    def test_test_plan_example_has_ui_layers(self):
        text = read("templates/loc/TEST-PLAN.md")
        self.assertRegex(text, r"\| ui \|[^\n]*Frontend")
        self.assertRegex(text, r"\| screenshots \|[^\n]*Frontend")


class PlanningUiTest(unittest.TestCase):
    def test_planning_puts_the_ui_layer_in_the_proof(self):
        text = read("skills/loc-planning/SKILL.md")
        rule = re.search(r"[^\n]*## Frontend[^\n]*", text).group(0)
        self.assertIn("**Proof:**", rule)
        self.assertIn("TEST-PLAN.md", rule)
        self.assertIn("**Manual check:**", rule)

    def test_brainstorm_records_a_visual_direction(self):
        text = read("skills/loc-brainstorm/SKILL.md")
        rule = re.search(r"[^\n]*## Frontend[^\n]*", text).group(0)
        self.assertIn("visual direction", rule)
        self.assertIn("decision", rule)
        self.assertRegex(rule, r"B-\d\d —")


class DesignReviewTest(unittest.TestCase):
    def test_review_runs_the_design_review_alongside(self):
        text = read("skills/loc-review/SKILL.md")
        step2 = section(text, "## 2. Review, in parallel")
        self.assertIn("## Frontend", step2)
        self.assertIn("`design-critic` agent in `full` mode", step2)
        self.assertIn("references/design.md", step2)
        self.assertIn("`Design plugin`", step2)
        self.assertIn("same step", step2)
        step3 = section(text, "## 3. Merge")
        self.assertIn("`[design]`", step3)


class DesignFlowTest(unittest.TestCase):
    """The plugin designs on its own: designer builds, ui_check.py measures, design-critic judges."""

    def test_reference_wires_the_agents_the_checks_and_the_sheet(self):
        text = read("skills/loc-orchestrate/references/design.md")
        for part in ("`designer` agent", "`design-critic` agent in `light` mode", "`design-critic` agent in `full` mode",
                     "ui_check.py --detect", "--check", "--tokens <Tokens>", "AskUserQuestion", "declined <date>",
                     "loc/tmp/design/references", "general words", "never assets", "checks.py --add", "--reference",
                     "--again", "at most 3 rounds"):
            self.assertIn(part, text)

    def test_skills_point_to_the_reference(self):
        for rel in ("skills/loc-orchestrate/SKILL.md", "skills/loc-planning/SKILL.md", "skills/loc-review/SKILL.md",
                    "skills/loc-brainstorm/SKILL.md", "skills/loc-init/SKILL.md"):
            self.assertIn("references/design.md", read(rel), rel)
        orchestrate = read("skills/loc-orchestrate/SKILL.md")
        self.assertIn("`designer` agent", orchestrate)
        self.assertIn("`design-critic` gate", orchestrate)
        self.assertIn("ui_check.py", read("skills/loc-planning/SKILL.md"))
        self.assertIn("ui_check.py", read("templates/CLAUDE.md"))

    def test_agents_build_and_judge_but_never_both(self):
        designer = read("agents/designer.md")
        critic = read("agents/design-critic.md")
        self.assertIn("tools: Read, Grep, Glob, Edit, Write", designer)
        self.assertIn("tools: Read, Grep, Glob\n", critic)
        for part in ("Second pass", "tokens file", "375 px", "never assets", "Never run commands"):
            self.assertIn(part, designer)
        for part in ("## Light", "## Full", "judged from code", "copy of one reference", "Findings: <n>"):
            self.assertIn(part, critic)


class ReadmeTest(unittest.TestCase):
    def test_readme_explains_frontend_projects(self):
        text = read("README.md")
        # The section quotes a `## Frontend` heading in a code block, so cut at the next section.
        body = text.split("## Frontend projects", 1)[1].split("\n## Guards", 1)[0]
        for part in ("## Frontend", "CLAUDE.md", "impeccable", "taste-skill", "loc-review", "proof"):
            self.assertIn(part, body)


if __name__ == "__main__":
    unittest.main()
