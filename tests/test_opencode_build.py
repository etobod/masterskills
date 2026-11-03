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
# Scratch directories stay inside the repository (nothing is written outside it), in an ignored directory.
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
        self.assertIn(f"{out.resolve().as_posix()}/masterskills/scripts/check_plan.py", orchestrate)

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
            for field in ("argument-hint", "context", "agent", "metadata"):
                self.assertNotRegex(head, rf"^{field}:", path)
            command = (out / "commands" / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn(f"Load the `{name}` skill", command)
            self.assertIn("$ARGUMENTS", command)
        qa = front((out / "commands" / "loc-qa.md").read_text(encoding="utf-8"))
        self.assertIn("agent: qa", qa)
        self.assertIn("subtask: true", qa)

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

    def test_agents_get_only_their_listed_tools(self):
        # Claude Code limits an agent to its `tools:`; OpenCode would otherwise give it
        # the web and every MCP server.
        out = self.scratch()
        self.run_build("--out", str(out))
        for name in ("rubber-duck", "judge", "code-review"):
            head = front((out / "agents" / f"{name}.md").read_text(encoding="utf-8"))
            lines = head.splitlines()
            self.assertIn('  "*": deny', lines, name)
            self.assertLess(lines.index('  "*": deny'), lines.index("  read: allow"), name)
            for tool in ("grep", "glob", "list"):
                self.assertIn(f"  {tool}: allow", lines, name)
            for tool in ("webfetch", "websearch", "task", "skill"):
                self.assertNotIn(f"  {tool}: allow", lines, name)
        qa = front((out / "agents" / "qa.md").read_text(encoding="utf-8")).splitlines()
        self.assertIn("  skill: allow", qa)
        base = out.resolve().as_posix()
        self.assertIn(f'    "{base}/masterskills/**": allow', qa)

    def test_code_review_is_an_agent(self):
        # Claude Code's code-review skill is built in; OpenCode gets an agent instead.
        out = self.scratch()
        self.run_build("--out", str(out))
        for path in out.rglob("*.md"):
            self.assertNotIn('Skill(skill: "code-review"', path.read_text(encoding="utf-8"), path)
        for rel, args in (("skills/loc-orchestrate/SKILL.md", '"<changed files> medium —'),
                          ("skills/loc-orchestrate/references/gates.md", '"<files review_diff listed> medium'),
                          ("skills/loc-review/SKILL.md", '"<changed files> <level> —')):
            text = (out / rel).read_text(encoding="utf-8")
            self.assertIn('task(subagent_type: "code-review", prompt: ' + args, text, rel)
        agent = front((out / "agents" / "code-review.md").read_text(encoding="utf-8"))
        self.assertIn("mode: subagent", agent)
        self.assertIn("edit: deny", agent)
        self.assertIn("bash: deny", agent)

    def test_ask_user_question_becomes_the_question_tool(self):
        out = self.scratch()
        self.run_build("--out", str(out))
        for path in out.rglob("*.md"):
            self.assertNotIn("AskUserQuestion", path.read_text(encoding="utf-8"), path)
        rules = (out / "masterskills" / "rules" / "core.md").read_text(encoding="utf-8")
        self.assertIn("also ask it with the `question` tool", rules)

    def test_installer_upgrades_opencode_first(self):
        lines = (ROOT / "opencode-install.bat").read_text(encoding="utf-8").splitlines()
        upgrade = next(i for i, line in enumerate(lines) if "winget upgrade --id SST.opencode -e" in line)
        self.assertLess(upgrade, next(i for i, line in enumerate(lines) if "git pull" in line))
        self.assertIn("where winget", lines[upgrade])
        self.assertNotIn("errorlevel", lines[upgrade + 1])

    def test_opencode_agents_are_measured(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from measure import measure
        items = {item["path"]: item for item in measure(ROOT)["items"]}
        self.assertEqual(items["opencode/agents/code-review.md"]["kind"], "agent")

    def test_the_hooks_plugin_points_at_the_install(self):
        out = self.scratch()
        self.run_build("--out", str(out))
        plugin = (out / "plugins" / "masterskills.ts").read_text(encoding="utf-8")
        self.assertNotIn("@@", plugin)
        self.assertIn(f'"{out.resolve().as_posix()}/masterskills"', plugin)
        self.assertNotIn("permission.ask", plugin)
        self.assertIn("MASTERSKILLS_PYTHON", plugin)
        hooks = json.loads((out / "masterskills" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("PreToolUse", hooks["hooks"])

    def test_script_commands_run_without_sh(self):
        # OpenCode on Windows runs commands in PowerShell, which has no `sh`.
        out = self.scratch()
        self.run_build("--out", str(out))
        for top in ("skills", "commands", "agents"):
            for path in (out / top).rglob("*.md"):
                self.assertNotIn("py.sh", path.read_text(encoding="utf-8"), path)
        review = (out / "skills" / "loc-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(review, r'\S -B "' + re.escape(out.resolve().as_posix()) + r'/masterskills/scripts/review_diff\.py"')

    def test_install_keeps_the_users_files_and_replaces_its_own(self):
        home = self.scratch()
        config = home / "opencode"
        (config / "skills" / "my-skill").mkdir(parents=True)
        (config / "skills" / "my-skill" / "SKILL.md").write_text("mine\n", encoding="utf-8")
        rules = (config / "masterskills" / "rules" / "core.md").resolve().as_posix()
        # 1.13.0 added the core rules to `instructions`; the hooks plugin now puts them in the prompt.
        mine = {"model": "local/qwen", "instructions": ["A.md", rules],
                "permission": {"bash": "ask", "external_directory": {"D:/data/**": "deny"}}}
        (config / "opencode.json").write_text(json.dumps(mine), encoding="utf-8")
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
        self.assertEqual(data["instructions"], ["A.md", "CLAUDE.md"])
        base = config.resolve().as_posix()
        self.assertEqual(data["permission"], {"bash": "ask", "external_directory": {
            "D:/data/**": "deny", f"{base}/masterskills/**": "allow", f"{base}/skills/**": "allow"}})
        version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        self.assertIn(f"masterskills {version}", result.stdout)
        self.assertIn("Restart OpenCode", result.stdout)

    def test_install_leaves_a_single_external_directory_value(self):
        home = self.scratch()
        config = home / "opencode"
        config.mkdir()
        (config / "opencode.json").write_text(json.dumps({"permission": {"external_directory": "ask"}}),
                                              encoding="utf-8")
        result = self.run_build("--install", config_home=home)
        data = json.loads((config / "opencode.json").read_text(encoding="utf-8"))
        self.assertEqual(data["permission"], {"external_directory": "ask"})
        self.assertEqual(data["instructions"], ["CLAUDE.md"])
        self.assertIn("add by hand", result.stdout)
        self.assertIn(f"{config.resolve().as_posix()}/masterskills/**", result.stdout)

    def test_install_does_not_touch_a_config_with_comments(self):
        home = self.scratch()
        config = home / "opencode"
        config.mkdir()
        text = '{\n  // my model\n  "model": "local/qwen"\n}\n'
        (config / "opencode.json").write_text(text, encoding="utf-8")
        result = self.run_build("--install", config_home=home)
        self.assertEqual((config / "opencode.json").read_text(encoding="utf-8"), text)
        self.assertIn('"instructions": ["CLAUDE.md"]', result.stdout)


if __name__ == "__main__":
    unittest.main()
