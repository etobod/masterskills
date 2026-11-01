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
        self.assertIn("design review", step2)
        self.assertIn("same step", step2)
        step3 = section(text, "## 3. Merge")
        self.assertIn("`[design]`", step3)


class ReadmeTest(unittest.TestCase):
    def test_readme_explains_frontend_projects(self):
        text = read("README.md")
        # The section quotes a `## Frontend` heading in a code block, so cut at the next section.
        body = text.split("## Frontend projects", 1)[1].split("\n## Guards", 1)[0]
        for part in ("## Frontend", "CLAUDE.md", "impeccable", "taste-skill", "loc-review", "proof"):
            self.assertIn(part, body)


if __name__ == "__main__":
    unittest.main()
