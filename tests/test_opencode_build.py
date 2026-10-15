"""Tests for opencode/build.py: the OpenCode version built from the Claude Code plugin."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch directories stay inside the repository (CLAUDE.md rule 1), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def front(text: str) -> str:
    return re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)


class OpenCodeBuildTest(unittest.TestCase):
    def scratch(self) -> Path:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def run_build(self, *args: str, config_home: Path = None) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        if config_home:
            env["XDG_CONFIG_HOME"] = str(config_home)
        result = subprocess.run([sys.executable, "-B", str(ROOT / "opencode" / "build.py"), *args],
                                capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_every_skill_and_agent_is_built_without_the_plugin_root(self):
        out = self.scratch()
        self.run_build("--out", str(out))
        for skill in (ROOT / "skills").iterdir():
            self.assertTrue((out / "skills" / skill.name / "SKILL.md").is_file(), skill.name)
        for agent in (ROOT / "agents").glob("*.md"):
            self.assertTrue((out / "agents" / agent.name).is_file(), agent.name)
        self.assertTrue((out / "masterskills" / "scripts" / "py.sh").is_file())
        self.assertTrue((out / "masterskills" / "rules" / "core.md").is_file())
        for path in out.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, path)
            self.assertNotRegex(text, r"masterskills:[a-z]", path)
        orchestrate = (out / "skills" / "loc-orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"{out.resolve().as_posix()}/masterskills/scripts/py.sh", orchestrate)

    def test_skill_front_matter_is_what_opencode_reads(self):
        out = self.scratch()
        self.run_build("--out", str(out))
        for path in (out / "skills").glob("*/SKILL.md"):
            head = front(path.read_text(encoding="utf-8"))
            name = re.search(r"^name: (.+)$", head, re.M).group(1)
            self.assertEqual(name, path.parent.name)
            self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
            description = json.loads(re.search(r"^description: (.+)$", head, re.M).group(1))
            self.assertTrue(1 <= len(description) <= 1024, path)
            self.assertIn('"opencode/slash": "true"', head)
            for field in ("argument-hint", "context", "agent"):
                self.assertNotRegex(head, rf"^{field}:", path)

    def test_agents_are_subagents_with_permissions(self):
        out = self.scratch()
        self.run_build("--out", str(out))
        judge = front((out / "agents" / "judge.md").read_text(encoding="utf-8"))
        self.assertIn("mode: subagent", judge)
        self.assertIn("edit: deny", judge)
        self.assertIn("bash: deny", judge)
        self.assertNotRegex(judge, r"^tools:")
        qa = front((out / "agents" / "qa.md").read_text(encoding="utf-8"))
        self.assertIn("edit: allow", qa)
        self.assertIn("bash: allow", qa)

    def test_the_hooks_plugin_points_at_the_install(self):
        out = self.scratch()
        self.run_build("--out", str(out))
        plugin = (out / "plugins" / "masterskills.ts").read_text(encoding="utf-8")
        self.assertNotIn("@@", plugin)
        self.assertIn(f'"{out.resolve().as_posix()}/masterskills"', plugin)
        self.assertIn(f'"{out.resolve().as_posix()}/skills"', plugin)
        hooks = json.loads((out / "masterskills" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("PreToolUse", hooks["hooks"])

    def test_install_keeps_the_users_files_and_replaces_its_own(self):
        home = self.scratch()
        config = home / "opencode"
        (config / "skills" / "my-skill").mkdir(parents=True)
        (config / "skills" / "my-skill" / "SKILL.md").write_text("mine\n", encoding="utf-8")
        rules = (config / "masterskills" / "rules" / "core.md").resolve().as_posix()
        # 1.13.0 added the core rules to `instructions`; the hooks plugin now puts them in the prompt.
        (config / "opencode.json").write_text(json.dumps({"model": "local/qwen", "instructions": ["A.md", rules]}),
                                              encoding="utf-8")
        self.run_build("--install", config_home=home)
        stale = config / "skills" / "loc-old" / "SKILL.md"
        stale.parent.mkdir()
        stale.write_text("old\n", encoding="utf-8")
        manifest = config / "masterskills" / "MANIFEST"
        manifest.write_text(manifest.read_text(encoding="utf-8") + "skills/loc-old/SKILL.md\n", encoding="utf-8")

        result = self.run_build("--install", config_home=home)

        self.assertFalse(stale.parent.exists())
        self.assertEqual((config / "skills" / "my-skill" / "SKILL.md").read_text(encoding="utf-8"), "mine\n")
        data = json.loads((config / "opencode.json").read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "local/qwen")
        self.assertEqual(data["instructions"], ["A.md"])
        version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        self.assertIn(f"masterskills {version}", result.stdout)
        self.assertIn("Restart OpenCode", result.stdout)

    def test_install_does_not_touch_a_config_with_comments(self):
        home = self.scratch()
        config = home / "opencode"
        config.mkdir()
        text = '{\n  // my model\n  "model": "local/qwen"\n}\n'
        (config / "opencode.json").write_text(text, encoding="utf-8")
        self.run_build("--install", config_home=home)
        self.assertEqual((config / "opencode.json").read_text(encoding="utf-8"), text)


if __name__ == "__main__":
    unittest.main()
