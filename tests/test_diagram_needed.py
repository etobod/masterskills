"""The overview is redrawn only when a plan changed the structure (B-16)."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scripts import ROOT, run, scratch_dir  # noqa: E402

OVERVIEW = "# Overview\n**Commit:** abc, 2026-11-25\n**Sources:** core/rules.py, db/store.py\n\n<diagram>\n"


class DiagramNeededTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        for rel, text in (("core/rules.py", "RULES = 1\n"), ("db/store.py", "STORE = 1\n"),
                          ("util/text.py", "TEXT = 1\n"), ("loc/diagrams/overview.md", OVERVIEW)):
            self.write(rel, text)
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       cwd=self.project, check=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.project, capture_output=True,
                              text=True, check=True).stdout.strip()
        self.write("loc/state/001.json", json.dumps({"milestones": [{"id": "M1", "start": head}]}))

    def write(self, rel: str, text: str) -> None:
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def needed(self) -> dict:
        out = run("diagram_needed.py", "--project", ".", "--state", "loc/state/001.json", cwd=self.project)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return json.loads(out.stdout)

    def test_a_new_code_file_needs_the_diagram(self):
        self.write("api/entries.py", "ENTRIES = 1\n")
        result = self.needed()
        self.assertTrue(result["needed"], result)
        self.assertEqual(result["files"], ["api/entries.py"])

    def test_a_deleted_code_file_needs_the_diagram(self):
        (self.project / "util" / "text.py").unlink()
        self.assertTrue(self.needed()["needed"])

    def test_a_changed_source_needs_the_diagram(self):
        self.write("core/rules.py", "RULES = 2\n")
        result = self.needed()
        self.assertTrue(result["needed"], result)
        self.assertIn("overview.md", result["reason"])

    def test_another_changed_file_does_not(self):
        # The overview was redrawn after every plan, whatever it changed (B-16).
        self.write("util/text.py", "TEXT = 2\n")
        self.write("README.md", "# Readme\n")
        self.write("loc/MEMORY.md", "x\n")
        result = self.needed()
        self.assertFalse(result["needed"], result)
        self.assertEqual(result["files"], [])

    def test_no_overview_yet_needs_it(self):
        (self.project / "loc" / "diagrams" / "overview.md").unlink()
        self.assertTrue(self.needed()["needed"])

    def test_orchestrate_draws_only_when_needed(self):
        text = (ROOT / "skills" / "loc-orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        journal = [line for line in text.splitlines() if line.startswith("5. **Journal.**")][0]
        self.assertIn("scripts/diagram_needed.py --state loc/state/<NNN>.json", journal)
        self.assertIn('only when it prints `"needed": true`', journal)


if __name__ == "__main__":
    unittest.main()
