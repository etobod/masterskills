"""End-to-end: the hooks run inside a real OpenCode, driven by a local stand-in model.

Nothing leaves the machine: the model is tests/fake_model.py on 127.0.0.1, which
answers each prompt with one scripted tool call. All OpenCode state lives in
`../tmp/masterskills/oc-e2e/` beside the repository (nothing is written outside it). Skipped without `opencode`.
"""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unittest
from pathlib import Path

from fake_model import FakeModel

ROOT = Path(__file__).resolve().parent.parent
E2E = ROOT.parent / "tmp" / "masterskills" / "oc-e2e"
OPENCODE = shutil.which("opencode")
ATTRIBUTION = "Co-authored-by: " + "Claude <noreply@anthropic.com>"


def remove(path: Path):
    """rmtree that also removes git's read-only object files on Windows."""
    def writable(func, name, _):
        os.chmod(name, stat.S_IWRITE)
        func(name)
    if path.exists():
        shutil.rmtree(path, onerror=writable)


@unittest.skipUnless(OPENCODE, "opencode is not on PATH")
class OpenCodeHooksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = FakeModel()
        cls.env = dict(os.environ, OPENCODE_DISABLE_CLAUDE_CODE="1")
        for kind in ("config", "data", "cache", "state"):
            cls.env[f"XDG_{kind.upper()}_HOME"] = str(E2E / kind)
        cls.config = E2E / "config" / "opencode"
        remove(cls.config)
        cls.config.mkdir(parents=True)
        provider = {"npm": "@ai-sdk/openai-compatible", "name": "fake",
                    "options": {"baseURL": f"http://127.0.0.1:{cls.model.port}/v1", "apiKey": "none"},
                    "models": {"fake": {"name": "fake", "tool_call": True}}}
        (cls.config / "opencode.json").write_text(json.dumps(
            {"model": "fake/fake", "autoupdate": False, "share": "disabled", "provider": {"fake": provider}}))
        subprocess.run([sys.executable, "-B", str(ROOT / "opencode" / "build.py"), "--install"],
                       env=cls.env, check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.model.close()

    def setUp(self):
        self.project = E2E / "project"
        remove(self.project)
        self.project.mkdir(parents=True)
        for command in (["init", "-q"], ["config", "user.name", "Test"], ["config", "user.email", "test@example.com"]):
            subprocess.run(["git", "-C", str(self.project), *command], check=True)

    def run_tool(self, tool: str, args: dict) -> str:
        """One OpenCode session in which the model calls `tool`; the result the model got back."""
        self.model.requests.clear()
        self.model.tool_call = (tool, args)
        result = subprocess.run([OPENCODE, "run", "go", "--auto", "--dir", str(self.project)], env=self.env,
                                capture_output=True, text=True, encoding="utf-8", timeout=180,
                                stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        answers = [m for m in self.model.requests[-1]["messages"] if m.get("role") == "tool"]
        self.assertEqual(len(answers), 1, "the model's tool call never ran")
        content = answers[0]["content"]
        return content if isinstance(content, str) else json.dumps(content)

    def commits(self) -> int:
        log = subprocess.run(["git", "-C", str(self.project), "rev-list", "--all", "--count"],
                             capture_output=True, text=True)
        return int(log.stdout.strip() or 0)

    def test_write_outside_the_project_is_refused(self):
        target = E2E / "outside.txt"
        target.unlink(missing_ok=True)
        answer = self.run_tool("write", {"filePath": target.as_posix(), "content": "x"})
        self.assertIn("files are written only inside the project", answer)
        self.assertFalse(target.exists())
        answer = self.run_tool("write", {"filePath": (self.project / "inside.txt").as_posix(), "content": "x"})
        self.assertTrue((self.project / "inside.txt").exists(), answer)

    def test_state_file_is_checked_after_a_write(self):
        state = (self.project / "loc" / "state" / "007.json").as_posix()
        answer = self.run_tool("write", {"filePath": state, "content": "{\"plan\": 1}}"})
        self.assertIn("not valid JSON", answer)
        answer = self.run_tool("write", {"filePath": (self.project / "notes.json").as_posix(), "content": "{"})
        self.assertNotIn("not valid JSON", answer)

    def test_commit_with_ai_attribution_is_refused(self):
        answer = self.run_tool("bash", {"command": f'git commit --allow-empty -m x -m "{ATTRIBUTION}"',
                                        "description": "commit"})
        self.assertIn("commits carry no AI attribution", answer)
        self.assertEqual(self.commits(), 0)
        self.run_tool("bash", {"command": "git commit --allow-empty -m x", "description": "commit"})
        self.assertEqual(self.commits(), 1)

    def test_core_rules_are_in_the_system_prompt_once(self):
        self.run_tool("bash", {"command": "echo hi", "description": "echo"})
        for request in self.model.requests:
            messages = [m for m in request["messages"] if m.get("role") == "system"]
            self.assertEqual(len(messages), 1, "strict chat templates accept one system message")
            system = json.dumps(messages, ensure_ascii=False)
            self.assertEqual(system.count("masterskills — core rules"), 1)

    def test_claude_md_is_read_next_to_agents_md(self):
        (self.project / "AGENTS.md").write_text("# Agents\nAGENTS-MARKER\n", encoding="utf-8")
        (self.project / "CLAUDE.md").write_text("# Project\nCLAUDE-MARKER\n", encoding="utf-8")
        self.run_tool("bash", {"command": "echo hi", "description": "echo"})
        system = json.dumps([m for m in self.model.requests[-1]["messages"] if m.get("role") == "system"])
        self.assertEqual(system.count("CLAUDE-MARKER"), 1)

    def test_loc_init_sets_up_the_project(self):
        skill = (self.config / "skills" / "loc-init" / "SKILL.md").read_text(encoding="utf-8")
        command = re.search(r"```sh\n(.+?init_project.+?)\n```", skill).group(1).replace("<dir>", self.project.as_posix())
        answer = self.run_tool("bash", {"command": command, "description": "loc-init"})
        self.assertTrue((self.project / "loc" / "inbox").is_dir(), answer)
        self.assertTrue((self.project / "CLAUDE.md").is_file(), answer)

    def test_skills_are_slash_commands(self):
        self.model.requests.clear()
        self.model.tool_call = None
        result = subprocess.run([OPENCODE, "run", "--command", "loc-init", "ARG-MARKER", "--auto", "--dir",
                                 str(self.project)], env=self.env, capture_output=True, text=True,
                                encoding="utf-8", timeout=180, stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        prompt = json.dumps([m for m in self.model.requests[-1]["messages"] if m.get("role") == "user"])
        self.assertIn("Load the `loc-init` skill", prompt)
        self.assertIn("ARG-MARKER", prompt)

    def test_shell_commands_see_the_plugin_root(self):
        answer = self.run_tool("bash", {"command": "echo ROOT=$CLAUDE_PLUGIN_ROOT", "description": "echo"})
        self.assertIn(f"ROOT={(self.config / 'masterskills').resolve().as_posix()}", answer)


if __name__ == "__main__":
    unittest.main()
