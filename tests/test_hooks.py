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
            f"{PY_SH} scripts/next_number.py --type question --slug \"a b\" --title \"T\" --source \"x\"",
            f"{PY_SH} scripts/mutate.py backup app.py",
            f"{PY_SH} scripts/mutate.py restore",
            f"{PY_SH} scripts/test_baseline.py --plan 007",
            'date "+%Y-%m-%d %H:%M"',
            "mv loc/inbox/001-question-a.md loc/inbox/done/",
            "mv loc/inbox/001-question-a.md loc/inbox/done/001-question-a.md",
            "gh run list --branch main --limit 1 --json status,conclusion,url",
            "gh run list --branch feature/ci-check --limit 1 --json status,conclusion,url",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.check(command), "allow")

    def test_leaves_everything_else_to_the_permission_rules(self):
        for command in (
            "mv inbox/001-question-a.md inbox/done/",
            "mv loc/inbox/001-a.md loc/inbox/done/ ; rm x",
            f"{PY_SH} scripts/next_number.py && rm x",
            f"{PY_SH} scripts/next_number.py > out.txt",
            f"{PY_SH} scripts/$(whoami).py",
            f"{PY_SH} scripts/missing.py",
            "mv loc/inbox/../CLAUDE.md loc/inbox/done/",
            "mv loc/inbox/*.md loc/inbox/done/",
            "cd x && date +%Y",
            "sh other/py.sh scripts/next_number.py",
            "gh run list --branch main --limit 1 --json status,conclusion,url ; rm x",
            "gh run list --branch main --limit 1 --json status,conclusion,url,logs",
            "gh run list --branch -R --limit 1 --json status,conclusion,url",
            "gh run rerun 123",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.check(command), "")

    def read(self, path: str) -> str:
        return decision(run_hook("plugin_commands.py", {"tool_name": "Read", "tool_input": {"file_path": path}}))

    def test_allows_reading_the_plugins_own_files(self):
        reference = ROOT / "skills" / "loc-planning" / "references" / "tests.md"
        for path in (str(reference), reference.as_posix(), "/" + reference.as_posix().replace(":", "", 1)):
            with self.subTest(path=path):
                self.assertEqual(self.read(path), "allow")

    def test_leaves_reads_outside_the_plugin_to_the_permission_rules(self):
        outside = Path(sys.executable).resolve()  # an existing file outside the plugin, nothing written
        paths = [str(outside), f"{ROOT.as_posix()}/skills/missing.md", str(ROOT.parent)]
        try:
            paths.append(f"{ROOT.as_posix()}/skills/{os.path.relpath(outside, ROOT / 'skills')}")
        except ValueError:  # another drive: no `..` path reaches it
            pass
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.read(path), "")

    def search(self, tool: str, tool_input: dict) -> str:
        return decision(run_hook("plugin_commands.py", {"tool_name": tool, "tool_input": tool_input}))

    def test_allows_listing_and_searching_inside_the_plugin(self):
        self.assertEqual(self.search("Glob", {"pattern": "templates/loc/*", "path": str(ROOT)}), "allow")
        self.assertEqual(self.search("Grep", {"pattern": "Criteria", "path": str(ROOT / "skills"),
                                              "glob": "*.md"}), "allow")

    def test_leaves_searches_that_leave_the_plugin_to_the_permission_rules(self):
        for tool, tool_input in (
            ("Glob", {"pattern": "*"}),
            ("Glob", {"pattern": "*", "path": str(ROOT.parent)}),
            ("Glob", {"pattern": "../*", "path": str(ROOT)}),
            ("Glob", {"pattern": "C:/Users/*", "path": str(ROOT)}),
            ("Grep", {"pattern": "x", "path": str(ROOT), "glob": "../**"}),
            ("Grep", {"pattern": "x", "path": f"{ROOT.as_posix()}/.."}),
        ):
            with self.subTest(tool=tool, tool_input=tool_input):
                self.assertEqual(self.search(tool, tool_input), "")

    def test_ignores_other_tools(self):
        out = run_hook("plugin_commands.py", {"tool_name": "PowerShell", "tool_input": {"command": "date +%Y"}})
        self.assertEqual(out, {})


class PyShTest(unittest.TestCase):
    def test_leaves_no_bytecode_in_the_plugin(self):
        plugin = scratch_dir(self)
        (plugin / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "py.sh", plugin / "scripts" / "py.sh")
        (plugin / "scripts" / "helper.py").write_text("VALUE = 'ok'\n", encoding="utf-8")
        (plugin / "scripts" / "main.py").write_text(
            "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent))\n"
            "from helper import VALUE\nprint(VALUE)\n", encoding="utf-8")
        result = subprocess.run(["sh", str(plugin / "scripts" / "py.sh"), "scripts/main.py"],
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "ok")
        self.assertEqual(list(plugin.rglob("__pycache__")), [])


class AfterPushTest(unittest.TestCase):
    def project(self, workflow: bool) -> Path:
        project = scratch_dir(self)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=project, check=True)
        if workflow:
            (project / ".github" / "workflows").mkdir(parents=True)
            (project / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
        return project

    def context(self, project: Path, command: str) -> str:
        out = run_hook("after_push.py", {"tool_name": "Bash", "tool_input": {"command": command},
                                         "cwd": str(project)}, {"CLAUDE_PROJECT_DIR": str(project)})
        return out.get("hookSpecificOutput", {}).get("additionalContext", "")

    def test_push_in_a_project_with_workflows_asks_for_one_ci_check(self):
        text = self.context(self.project(True), "git push origin main")
        self.assertIn("gh run list --branch main --limit 1 --json status,conclusion,url", text)
        self.assertIn("--type stuck", text)

    def test_push_without_workflows_adds_nothing(self):
        self.assertEqual(self.context(self.project(False), "git push"), "")

    def test_other_commands_add_nothing(self):
        project = self.project(True)
        for command in ("git status", "git push && rm x", "echo git push"):
            with self.subTest(command=command):
                self.assertEqual(self.context(project, command), "")


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

    def settings(self, name: str, text: str) -> None:
        path = Path(self.project) / ".claude" / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_additional_directories_of_the_project_are_allowed(self):
        data = scratch_dir(self)
        other = scratch_dir(self)
        self.settings("settings.json", json.dumps({"permissions": {"additionalDirectories": [str(data / "reports")]}}))
        self.settings("settings.local.json", json.dumps({"permissions": {"additionalDirectories": ["../shared"]}}))
        self.assertEqual(self.check("Write", {"file_path": str(data / "reports" / "r.md")}), {})
        self.assertEqual(self.check("Write", {"file_path": str(Path(self.project).parent / "shared" / "a.md")}), {})
        self.assertEqual(self.check("Bash", {"command": f'echo x > "{(data / "reports" / "b.md").as_posix()}"'}), {})
        self.assertEqual(decision(self.check("Write", {"file_path": str(data / "reports-old" / "r.md")})), "deny")
        self.assertEqual(decision(self.check("Write", {"file_path": str(other / "r.md")})), "deny")

    def test_bad_settings_give_no_exceptions(self):
        data = scratch_dir(self)
        for text in ("{not json", json.dumps({"permissions": {"additionalDirectories": str(data)}})):
            self.settings("settings.json", text)
            self.assertEqual(decision(self.check("Write", {"file_path": str(data / "r.md")})), "deny", text)


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
        (project / "loc" / "inbox" / "001-question-a.md").write_text("# 001 — Pytanie A\n\n**Type:** question\n",
                                                                     encoding="utf-8")
        text = self.context(project)
        self.assertIn("loc/inbox/001-question-a.md", text)
        self.assertIn("mv loc/inbox/<file> loc/inbox/done/", text)

    def test_inbox_command_follows_the_python_of_opencode(self):
        project = scratch_dir(self)
        (project / "loc" / "inbox" / "done").mkdir(parents=True)
        env = {"CLAUDE_PROJECT_DIR": str(project), "CLAUDE_PLUGIN_ROOT": "C:/oc/masterskills"}
        out = run_hook("session_start.py", {"cwd": str(project)}, {**env, "MASTERSKILLS_PYTHON": "python"})
        self.assertIn('`python -B "C:/oc/masterskills/scripts/next_number.py" --type',
                      out["hookSpecificOutput"]["additionalContext"])
        out = run_hook("session_start.py", {"cwd": str(project)}, {**env, "MASTERSKILLS_PYTHON": ""})
        self.assertIn('`sh "C:/oc/masterskills/scripts/py.sh" scripts/next_number.py --type',
                      out["hookSpecificOutput"]["additionalContext"])

    def test_session_start_asks_for_migration(self):
        project = scratch_dir(self)
        (project / "loc" / "inbox").mkdir(parents=True)
        self.assertIn("/masterskills:loc-init to migrate loc/ to format 2", self.context(project))
        (project / "loc" / "VERSION").write_text("2\n", encoding="utf-8")
        self.assertNotIn("migrate", self.context(project))

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
        self.assertFalse((project / "loc" / "state" / "mutation.json").exists())
        self.assertNotIn("Interrupted mutation", self.context(project))


if __name__ == "__main__":
    unittest.main()
