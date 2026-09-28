"""Tests for the plugin's hooks: each hook runs as Claude Code runs it, JSON on stdin."""

import hashlib
import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch projects stay inside the repository (CLAUDE.md rule 1), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def scratch_dir(test: unittest.TestCase) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=SCRATCH))
    test.addCleanup(shutil.rmtree, path, True)
    return path
PY_SH = f'sh "{ROOT.as_posix()}/scripts/py.sh"'


def run_hook(name: str, data: dict, env: dict = None) -> dict:
    result = subprocess.run(
        [sys.executable, str(ROOT / "hooks" / name)],
        input=json.dumps(data), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, **(env or {})}, check=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def decision(output: dict) -> str:
    return output.get("hookSpecificOutput", {}).get("permissionDecision", "")


class PluginCommandsTest(unittest.TestCase):
    def check(self, command: str) -> str:
        return decision(run_hook("plugin_commands.py", {"tool_name": "Bash", "tool_input": {"command": command}}))

    def test_allows_the_skills_commands(self):
        for command in (
            f"{PY_SH} scripts/next_number.py --type pytanie --slug \"a b\" --title \"T\" --source \"x\"",
            f"{PY_SH} scripts/mutate.py backup app.py",
            f"{PY_SH} scripts/mutate.py restore",
            f"{PY_SH} scripts/test_baseline.py --plan 007",
            'date "+%Y-%m-%d %H:%M"',
            "mv loc/inbox/001-pytanie-a.md loc/inbox/done/",
            "mv loc/inbox/001-pytanie-a.md loc/inbox/done/001-pytanie-a.md",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.check(command), "allow")

    def test_leaves_everything_else_to_the_permission_rules(self):
        for command in (
            "mv inbox/001-pytanie-a.md inbox/done/",
            "mv loc/inbox/001-a.md loc/inbox/done/ ; rm x",
            f"{PY_SH} scripts/next_number.py && rm x",
            f"{PY_SH} scripts/next_number.py > out.txt",
            f"{PY_SH} scripts/$(whoami).py",
            f"{PY_SH} scripts/missing.py",
            "mv loc/inbox/../CLAUDE.md loc/inbox/done/",
            "mv loc/inbox/*.md loc/inbox/done/",
            "cd x && date +%Y",
            "sh other/py.sh scripts/next_number.py",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.check(command), "")

    def test_ignores_other_tools(self):
        out = run_hook("plugin_commands.py", {"tool_name": "PowerShell", "tool_input": {"command": "date +%Y"}})
        self.assertEqual(out, {})


class WriteGuardTest(unittest.TestCase):
    def setUp(self):
        self.project = str(scratch_dir(self))

    def check(self, tool: str, tool_input: dict) -> dict:
        return run_hook("write_guard.py", {"tool_name": tool, "tool_input": tool_input, "cwd": self.project},
                        {"CLAUDE_PROJECT_DIR": self.project})

    def test_denies_writes_outside_the_project_and_points_to_loc(self):
        out = self.check("Write", {"file_path": str(Path.home() / ".claude" / "plans" / "a.md")})
        self.assertEqual(decision(out), "deny")
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("loc/PATTERNS.md", reason)
        self.assertIn("loc/tmp/", reason)

    def test_allows_writes_inside_the_project(self):
        self.assertEqual(self.check("Write", {"file_path": str(Path(self.project) / "loc" / "tmp" / "a.txt")}), {})


class CommitGuardTest(unittest.TestCase):
    def check(self, command: str) -> str:
        return decision(run_hook("commit_guard.py", {"tool_name": "Bash", "tool_input": {"command": command}}))

    def test_denies_attribution_markers(self):
        self.assertEqual(self.check('git commit -m "x\n\nCo-authored-by: Claude <noreply@anthropic.com>"'), "deny")

    def test_allows_a_plain_commit(self):
        self.assertEqual(self.check('git commit -m "feat: add Claude API client"'), "")


class SessionStartTest(unittest.TestCase):
    def context(self, project: Path) -> str:
        out = run_hook("session_start.py", {"cwd": str(project)}, {"CLAUDE_PROJECT_DIR": str(project)})
        return out["hookSpecificOutput"]["additionalContext"]

    def test_lists_open_loc_inbox_files_and_commands(self):
        project = scratch_dir(self)
        (project / "loc" / "inbox" / "done").mkdir(parents=True)
        (project / "loc" / "inbox" / "001-pytanie-a.md").write_text("# 001 — Pytanie A\n\n**Typ:** pytanie\n",
                                                                     encoding="utf-8")
        text = self.context(project)
        self.assertIn("loc/inbox/001-pytanie-a.md", text)
        self.assertIn("mv loc/inbox/<file> loc/inbox/done/", text)

    def test_project_without_loc(self):
        self.assertIn("no `loc/inbox/` yet", self.context(scratch_dir(self)))

    def test_restores_a_file_left_mutated(self):
        project = scratch_dir(self)
        app = project / "app.py"
        app.write_text("good\n", encoding="utf-8")
        original = hashlib.sha256(app.read_bytes()).hexdigest()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "mutate.py"), "backup", "app.py"], cwd=project,
                       capture_output=True, check=True)
        app.write_text("mutated\n", encoding="utf-8")
        text = self.context(project)
        self.assertIn("Restored `app.py`", text)
        self.assertEqual(hashlib.sha256(app.read_bytes()).hexdigest(), original)
        self.assertFalse((project / "loc" / "state" / "mutacja.json").exists())
        self.assertNotIn("Interrupted mutation", self.context(project))


if __name__ == "__main__":
    unittest.main()
