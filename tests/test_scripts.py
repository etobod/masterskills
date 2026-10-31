"""Tests for the scripts that create and read the project's `loc/` files."""

import json
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


def run(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8")


class InitProjectTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)

    def test_creates_loc_and_one_ignore_line_idempotently(self):
        first = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)
        second = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)
        for rel in ("loc/inbox/done", "loc/PRD.md", "loc/PATTERNS.md", "loc/MEMORY.md"):
            self.assertTrue((self.project / rel).exists(), rel)
        self.assertFalse((self.project / "inbox").exists())
        self.assertFalse((self.project / "docs").exists())
        lines = (self.project / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count("loc/"), 1)
        self.assertIn(".gitignore", first["created"])
        self.assertEqual(second["created"] + second["updated"], [])

    def test_new_loc_gets_the_current_format_and_an_old_one_does_not(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        self.assertEqual((self.project / "loc" / "VERSION").read_text(encoding="utf-8").strip(), "4")
        old = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=old, check=True)
        (old / "loc" / "inbox").mkdir(parents=True)
        run("init_project.py", "--project", ".", cwd=old)
        self.assertFalse((old / "loc" / "VERSION").exists())

    def test_test_plan_comes_only_from_a_plan(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        self.assertFalse((self.project / "loc" / "TEST-PLAN.md").exists())
        self.assertIn("## Project-specific workflow", (self.project / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_diagrams_have_a_kept_and_a_tmp_directory(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        self.assertTrue((self.project / "loc" / "diagrams" / "tmp").is_dir())
        self.assertIn("## Diagrams", (self.project / "CLAUDE.md").read_text(encoding="utf-8"))
        root = Path(__file__).resolve().parent.parent
        orchestrate = (root / "skills" / "loc-orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('Skill(skill: "masterskills:loc-diagram", args: "overview")', orchestrate)

    def test_reports_the_empty_sections_a_brainstorm_may_fill(self):
        fresh = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)["empty"]
        self.assertEqual(fresh["loc/PRD.md"], ["Goal", "Core idea", "Scenarios"])
        self.assertIn("Commands", fresh["CLAUDE.md"])
        self.assertIn("Limits", fresh["CLAUDE.md"])
        claude = self.project / "CLAUDE.md"
        text = claude.read_text(encoding="utf-8").replace("## Limits\n", "## Limits\nNo cloud services.\n")
        claude.write_text(text, encoding="utf-8")
        prd = self.project / "loc" / "PRD.md"
        prd.write_text(prd.read_text(encoding="utf-8").replace(
            "## Goal\n", "## Goal\nA diary that stays offline.\n"), encoding="utf-8")
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        again = json.loads(run("init_project.py", "--project", ".", cwd=self.project).stdout)["empty"]
        self.assertNotIn("Limits", again["CLAUDE.md"])
        self.assertIn("Commands", again["CLAUDE.md"])
        self.assertEqual(again["loc/PRD.md"], ["Core idea", "Scenarios"])
        after = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)

    def test_check_reports_without_writing(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        claude = self.project / "CLAUDE.md"
        text = claude.read_text(encoding="utf-8").replace("## Limits\n", "## Limits\nJeden plik, zero zależności.\n")
        text = text.replace("## Invariants\n", "## Invariants\n- One file only.\n")
        claude.write_text(text, encoding="utf-8")
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        out = run("init_project.py", "--project", ".", "--check", cwd=self.project)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertIn("Goal", result["empty"]["loc/PRD.md"])
        self.assertEqual(result["not_english"], ["Limits"])
        self.assertNotIn("created", result)
        after = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)

    def test_check_reports_a_missing_prd_section(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        prd = self.project / "loc" / "PRD.md"
        prd.write_text("# PRD\n\n## Goal\nA diary.\n\n## Core idea\n- Offline.\n\n## Directions\n", encoding="utf-8")
        before = prd.read_bytes()
        result = json.loads(run("init_project.py", "--project", ".", "--check", cwd=self.project).stdout)
        self.assertEqual(result["empty"]["loc/PRD.md"], ["Scenarios"])
        self.assertEqual(prd.read_bytes(), before)

    def test_git_sees_nothing_from_loc(self):
        run("init_project.py", "--project", ".", cwd=self.project)
        status = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=self.project,
                                capture_output=True, text=True, check=True).stdout
        self.assertNotIn("loc/", status)


class NextNumberTest(unittest.TestCase):
    def test_numbers_across_inbox_and_done_and_creates_the_file(self):
        project = scratch_dir(self)
        (project / "loc" / "inbox" / "done").mkdir(parents=True)
        (project / "loc" / "inbox" / "done" / "004-plan-a.md").write_text("x", encoding="utf-8")
        out = run("next_number.py", "--project", ".", "--type", "deferred", "--slug", "later", "--title", "Later",
                  "--source", "test", "--by", "loc-qa", cwd=project)
        result = json.loads(out.stdout)
        self.assertEqual(result["number"], "005")
        self.assertEqual(result["path"], "loc/inbox/005-deferred-later.md")
        self.assertTrue((project / result["path"]).is_file())

    def test_question_has_english_headings_and_old_types_are_rejected(self):
        project = scratch_dir(self)
        out = run("next_number.py", "--project", ".", "--type", "question", "--slug", "colour", "--title", "Colour",
                  "--source", "test", "--by", "loc-planning", cwd=project)
        text = (project / json.loads(out.stdout)["path"]).read_text(encoding="utf-8")
        for heading in ("**Type:** question", "## Question", "## Options", "## Interim", "## Resolution"):
            self.assertIn(heading, text)
        old = run("next_number.py", "--project", ".", "--type", "pytanie", "--slug", "x", "--title", "X",
                  "--source", "test", cwd=project)
        self.assertNotEqual(old.returncode, 0)

    def test_question_names_who_recommends(self):
        project = scratch_dir(self)
        base = ("next_number.py", "--project", ".", "--slug", "x", "--title", "X", "--source", "test")
        out = run(*base, "--type", "question", cwd=project)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((project / "loc" / "inbox").exists() and any((project / "loc" / "inbox").iterdir()))
        out = run(*base, "--type", "question", "--by", "architect (Triage)", cwd=project)
        text = (project / json.loads(out.stdout)["path"]).read_text(encoding="utf-8")
        self.assertIn("**Recommended by:** architect (Triage)\n", text)
        self.assertNotIn("**Created by:**", text)

    def test_stuck_shows_gate_and_verdict_first(self):
        text = (ROOT / "templates" / "loc" / "inbox" / "stuck.md").read_text(encoding="utf-8")
        self.assertLess(text.index("**Stuck gates:**"), text.index("\n## "))
        order = [text.index(marker) for marker in
                 ("**Gate:**", "**Architect", "**Next:**", "### What remains", "### Rounds")]
        self.assertEqual(order, sorted(order))

    def test_every_file_names_its_author(self):
        project = scratch_dir(self)
        base = ("next_number.py", "--project", ".", "--title", "X", "--source", "test")
        out = run(*base, "--type", "deferred", "--slug", "x", cwd=project)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((project / "loc" / "inbox").exists() and any((project / "loc" / "inbox").iterdir()))
        for kind in ("brainstorm", "plan", "deferred", "review", "stuck"):
            out = run(*base, "--type", kind, "--slug", kind, "--by", "loc-orchestrate", cwd=project)
            self.assertEqual(out.returncode, 0, out.stderr)
            text = (project / json.loads(out.stdout)["path"]).read_text(encoding="utf-8")
            self.assertIn("**Created by:** loc-orchestrate\n", text, kind)

    def test_deferred_sections_from_options(self):
        project = scratch_dir(self)
        out = run("next_number.py", "--project", ".", "--type", "deferred", "--slug", "ui check",
                  "--title", "UI check", "--source", "loc-qa 008",
                  "--what", "Open the page: the overlay toggles", "--why", "user (deferrable)",
                  "--when", "next time the page is opened", "--by", "loc-qa", cwd=project)
        text = (project / json.loads(out.stdout)["path"]).read_text(encoding="utf-8")
        self.assertIn("## What was deferred\nOpen the page: the overlay toggles\n", text)
        self.assertIn("## Why not now\nuser (deferrable)\n", text)
        self.assertIn("## When to return\nnext time the page is opened\n", text)
        self.assertNotIn("<the work to do", text)
        self.assertIn("## Resolution\n<empty until handled", text)

    def test_section_option_needs_the_section(self):
        project = scratch_dir(self)
        out = run("next_number.py", "--project", ".", "--type", "question", "--slug", "x", "--title", "X",
                  "--what", "something", cwd=project)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((project / "loc" / "inbox").exists() and any((project / "loc" / "inbox").iterdir()))


class ReviewDiffTest(unittest.TestCase):
    def test_review_without_commits(self):
        project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        (project / "app.js").write_text("const x = 1;\n", encoding="utf-8")
        (project / "loc").mkdir()
        (project / "loc" / "notes.md").write_text("x\n", encoding="utf-8")
        out = run("review_diff.py", "--project", ".", "--from", "HEAD", "--out", "loc/review/x.diff", cwd=project)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual(result["files"], ["app.js"])
        self.assertIn("+const x = 1;", (project / "loc" / "review" / "x.diff").read_text(encoding="utf-8"))


@unittest.skipUnless(sys.platform == "win32", "launchers are .bat files")
class LauncherTest(unittest.TestCase):
    """loc-init leaves a launcher for the tool that ran it, and never touches an existing one."""
    SESSION = "4850f8d8-961b-41b6-af2d-aa21b2b73f24"

    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)

    def init(self, *args: str, scripts: Path = ROOT / "scripts") -> dict:
        out = subprocess.run([sys.executable, "-B", str(scripts / "init_project.py"), "--project", ".", *args],
                             cwd=self.project, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_claude_bat_resumes_the_session(self):
        report = self.init("--session", self.SESSION)
        self.assertIn("claude.bat", report["created"])
        data = (self.project / "claude.bat").read_bytes()
        self.assertIn(b"\r\n", data)
        self.assertIn(f"--resume {self.SESSION}".encode(), data)
        # In its own directory `claude` is this very file: the launcher must name claude.exe.
        self.assertNotIn(b'"CLAUDE=claude"', data)
        self.assertIn(b"where claude.exe", data)
        self.assertFalse((self.project / "open-code.bat").exists())
        again = self.init("--session", "11111111-2222-3333-4444-555555555555")
        self.assertIn("claude.bat", again["existing"])
        self.assertEqual((self.project / "claude.bat").read_bytes(), data)

    def test_claude_bat_repairs_the_old_launcher(self):
        broken = "\r\n".join([
            "@rem Resumes the Claude Code session in which loc-init ran.",
            '@cd /d "%~dp0"',
            '@set "CLAUDE=claude"',
            r'@where claude >nul 2>nul || set "CLAUDE=%USERPROFILE%\.local\bin\claude.exe"',
            '@"%CLAUDE%" --resume abc-1 %*',
            "@exit /b %ERRORLEVEL%",
            ""])
        (self.project / "claude.bat").write_bytes(broken.encode("utf-8"))
        report = self.init("--session", self.SESSION)
        data = (self.project / "claude.bat").read_bytes()
        self.assertIn("claude.bat", [item["path"] for item in report["updated"]])
        self.assertIn(b"--resume abc-1 %*", data)
        self.assertIn(b"where claude.exe", data)
        self.assertNotIn(b'"CLAUDE=claude"', data)
        own = b"@claude --resume mine\r\n"
        (self.project / "claude.bat").write_bytes(own)
        self.assertIn("claude.bat", self.init("--session", self.SESSION)["existing"])
        self.assertEqual((self.project / "claude.bat").read_bytes(), own)

    def test_claude_bat_needs_a_session(self):
        report = self.init()
        self.assertFalse((self.project / "claude.bat").exists())
        self.assertIn("claude.bat", [item["path"] for item in report["skipped"]])

    def test_open_code_bat_updates_the_plugin(self):
        build = scratch_dir(self)
        subprocess.run([sys.executable, "-B", str(ROOT / "opencode" / "build.py"), "--out", str(build)],
                       check=True, capture_output=True)
        report = self.init("--session", "${CLAUDE_SESSION_ID}", scripts=build / "masterskills" / "scripts")
        self.assertIn("open-code.bat", report["created"])
        self.assertFalse((self.project / "claude.bat").exists())
        text = (self.project / "open-code.bat").read_text(encoding="utf-8")
        self.assertIn(f'call "{ROOT / "opencode-install.bat"}"', text)
        self.assertIn("opencode %*", text)


if __name__ == "__main__":
    unittest.main()


class PlanQueueTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        self.inbox = self.project / "loc" / "inbox"
        (self.inbox / "done").mkdir(parents=True)
        (self.project / "loc" / "state").mkdir()

    def write(self, rel: str, text: str = "x\n") -> Path:
        path = self.project / rel
        path.write_text(text, encoding="utf-8")
        return path

    def queue(self, *args: str) -> dict:
        result = run("plan_queue.py", "--project", ".", *args, cwd=self.project)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_lists_open_plans_in_group_order(self):
        for name in ("071-plan-2-hard-b.md", "070-plan-2-easy-a.md", "072-plan-1-medium-c.md",
                     "060-plan-old-topic.md", "073-brainstorm-x.md", "done/050-plan-1-easy-z.md"):
            self.write(f"loc/inbox/{name}")
        names = [Path(p["path"]).name for p in self.queue()["queue"]]
        self.assertEqual(names, ["060-plan-old-topic.md", "072-plan-1-medium-c.md",
                                 "070-plan-2-easy-a.md", "071-plan-2-hard-b.md"])

    def test_make_room_shifts_groups_and_references(self):
        self.write("loc/inbox/070-plan-1-easy-a.md")
        self.write("loc/inbox/071-plan-2-hard-b.md", "**Source:** loc/inbox/done/069-brainstorm-x.md\n")
        self.write("loc/inbox/072-plan-1-medium-run.md")
        self.write("loc/inbox/075-plan-1-easy-urgent.md")
        self.write("loc/inbox/done/069-brainstorm-x.md", "→ plan loc/inbox/071-plan-2-hard-b.md (2026-10-18)\n")
        self.write("loc/inbox/074-deferred-y.md", "**Source:** loc/inbox/070-plan-1-easy-a.md\n")
        self.write("loc/state/072.json", json.dumps({"plan": "loc/inbox/072-plan-1-medium-run.md", "phase": "build"}))
        self.write("loc/state/070.json", json.dumps({"plan": "loc/inbox/070-plan-1-easy-a.md", "phase": "done"}))
        self.write("loc/MEMORY.md", "Details: loc/inbox/071-plan-2-hard-b.md\n")
        self.queue("--make-room", "1", "--keep", "075")
        names = sorted(p.name for p in self.inbox.glob("*-plan-*.md"))
        self.assertEqual(names, ["070-plan-2-easy-a.md", "071-plan-3-hard-b.md",
                                 "072-plan-1-medium-run.md", "075-plan-1-easy-urgent.md"])
        read = lambda rel: (self.project / rel).read_text(encoding="utf-8")
        self.assertIn("loc/inbox/071-plan-3-hard-b.md", read("loc/inbox/done/069-brainstorm-x.md"))
        self.assertIn("loc/inbox/070-plan-2-easy-a.md", read("loc/inbox/074-deferred-y.md"))
        self.assertIn("loc/inbox/070-plan-2-easy-a.md", read("loc/state/070.json"))
        self.assertIn("loc/inbox/071-plan-3-hard-b.md", read("loc/MEMORY.md"))
        self.assertIn("072-plan-1-medium-run.md", read("loc/state/072.json"))

    def test_set_assigns_groups(self):
        self.write("loc/inbox/070-plan-easy-a.md")
        self.write("loc/inbox/068-plan-1-medium-b.md")
        self.write("loc/inbox/060-plan-c.md")
        self.write("loc/inbox/061-plan-run.md")
        self.write("loc/state/061.json", json.dumps({"plan": "loc/inbox/061-plan-run.md", "phase": "build"}))
        self.write("loc/MEMORY.md", "Details: loc/inbox/070-plan-easy-a.md, loc/inbox/060-plan-c.md\n")
        out = self.queue("--set", "070=1", "--set", "068=2", "--set", "060=3", "--set", "061=4")
        names = sorted(p.name for p in self.inbox.glob("*-plan-*.md"))
        self.assertEqual(names, ["060-plan-3-c.md", "061-plan-run.md", "068-plan-2-medium-b.md",
                                 "070-plan-1-easy-a.md"])
        memory = (self.project / "loc/MEMORY.md").read_text(encoding="utf-8")
        self.assertIn("loc/inbox/070-plan-1-easy-a.md", memory)
        self.assertIn("loc/inbox/060-plan-3-c.md", memory)
        self.assertEqual(out["skipped"], ["061"])
        self.assertEqual([p["number"] for p in out["queue"]], ["061", "070", "068", "060"])
        self.assertEqual(out["queue"][3]["group"], 3)

    def test_skills_use_the_queue(self):
        planning = (ROOT / "skills" / "loc-planning" / "SKILL.md").read_text(encoding="utf-8")
        orchestrate = (ROOT / "skills" / "loc-orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("plan_queue.py --set", planning)
        self.assertIn("plan_queue.py", orchestrate)
