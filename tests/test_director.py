"""The director: a course agreed with the user in loc/PRD.md `## Course`, its status and the Stop hook."""

import datetime
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
SCRATCH = ROOT / "tmp" / "scratch" / "tests"
PRD = "# PRD — x\n\n## Goal\nGreet people.\n\n## Decisions\n- D-01: Plain text. Reason: simple. (2026-01-01)\n"


def project(test: unittest.TestCase, prd: str = PRD) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=SCRATCH))
    test.addCleanup(shutil.rmtree, path, True)
    (path / "loc" / "inbox" / "done").mkdir(parents=True)
    if prd is not None:
        (path / "loc" / "PRD.md").write_text(prd, encoding="utf-8")
    return path


def course(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "course.py"), *args, "--project", str(cwd)],
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd, env=env)


def section(cwd: Path) -> str:
    text = (cwd / "loc" / "PRD.md").read_text(encoding="utf-8")
    return text.split("## Course")[1]


def stop_hook(cwd: Path, active: bool = False) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    data = {"hook_event_name": "Stop", "cwd": str(cwd), "stop_hook_active": active}
    return subprocess.run([sys.executable, "-B", str(ROOT / "hooks" / "director_stop.py")], input=json.dumps(data),
                          capture_output=True, text=True, encoding="utf-8", env=env)


def minutes(delta: int) -> str:
    return (datetime.datetime.now() + datetime.timedelta(minutes=delta)).strftime("%Y-%m-%d %H:%M")


class CourseTest(unittest.TestCase):
    def test_start_writes_the_course(self):
        cwd = project(self)
        result = course(cwd, "start", "--limit", "goal", "--agreed", "plan 084, then 087",
                        "--item", "plan 084", "--item", "plan 087")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = section(cwd)
        for marker in ("**State:** open", "**Limit:** goal", "**Steps:** 0 of 12", "**Next:**",
                       "**Last report to the user:**", "- [ ] plan 084 — agreed", "- [ ] plan 087 — agreed"):
            self.assertIn(marker, text)
        self.assertRegex(text, r"\*\*Agreed:\*\* \d{4}-\d{2}-\d{2} \d{2}:\d{2} — plan 084, then 087")
        self.assertIn("## Goal\nGreet people.", (cwd / "loc" / "PRD.md").read_text(encoding="utf-8"))
        self.assertEqual(course(cwd, "start", "--limit", "none", "--agreed", "x").returncode, 1)

    def test_bad_limit_is_refused(self):
        cwd = project(self)
        self.assertEqual(course(cwd, "start", "--limit", "tomorrow", "--agreed", "x").returncode, 2)
        self.assertEqual(course(cwd, "start", "--limit", "until 2026-10-22 21:00", "--agreed", "x").returncode, 0)
        self.assertIn("**Limit:** until 2026-10-22 21:00", section(cwd))

    def test_next_add_done_stop(self):
        cwd = project(self)
        course(cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "plan 084")
        self.assertEqual(course(cwd, "next", "--text", "loc-orchestrate 084").returncode, 0)
        self.assertIn("**Next:** loc-orchestrate 084", section(cwd))
        self.assertEqual(course(cwd, "add", "--item", "plan the leftovers").returncode, 2)
        added = course(cwd, "add", "--item", "plan 091", "--source", "loc/inbox/091-stuck-x.md (plan 084)")
        self.assertEqual(added.returncode, 0, added.stderr)
        self.assertIn("- [ ] plan 091 — from loc/inbox/091-stuck-x.md (plan 084)", section(cwd))
        self.assertEqual(course(cwd, "done", "--item", "plan 084").returncode, 0)
        self.assertIn("- [x] plan 084 — agreed", section(cwd))
        self.assertEqual(course(cwd, "done", "--item", "plan 999").returncode, 1)
        self.assertEqual(course(cwd, "stop", "--reason", "the user said stop").returncode, 0)
        self.assertRegex(section(cwd), r"\*\*State:\*\* closed \d{4}-\d{2}-\d{2} \d{2}:\d{2} — the user said stop")
        self.assertEqual(course(cwd, "start", "--limit", "goal", "--agreed", "again").returncode, 0)
        self.assertEqual(section(cwd).count("**State:**"), 1)

    def test_template_describes_the_course(self):
        template = (ROOT / "templates" / "loc" / "PRD.md").read_text(encoding="utf-8")
        self.assertIn("## Course", template)
        self.assertIn("loc-director", template)


class StatusTest(unittest.TestCase):
    def test_status_prints_fixed_sections(self):
        cwd = project(self)
        course(cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "plan 084", "--item", "plan 087")
        prd = cwd / "loc" / "PRD.md"
        text = prd.read_text(encoding="utf-8")
        text = re.sub(r"\*\*Last report to the user:\*\* .*", "**Last report to the user:** 2026-10-22 10:00", text)
        text = text.replace("(2026-01-01)\n", "(2026-01-01)\n- D-02: One file. Reason: no extra files. (2026-10-22)\n")
        prd.write_text(text, encoding="utf-8")
        course(cwd, "done", "--item", "plan 084")
        course(cwd, "next", "--text", "loc-planning 087")
        (cwd / "loc" / "MEMORY.md").write_text(
            "# Memory\n\n## 2026-10-22 11:00 — [Plan] Greeting\nDone.\n\n## 2026-10-21 09:00 — [Plan] Old\nOld.\n",
            encoding="utf-8")
        inbox = cwd / "loc" / "inbox"
        (inbox / "092-U-question-cache.md").write_text("# 092 — Cache?\n\n**Created:** 2026-10-22 11:30\n",
                                                       encoding="utf-8")
        (inbox / "091-stuck-greeting.md").write_text(
            "# 091 — Greeting stuck\n\n**Created:** 2026-10-22 11:10\n"
            "**Architect (Triage):** plan — one cache module — cost if wrong: one file (architect, 2026-10-22)\n",
            encoding="utf-8")
        (inbox / "080-deferred-old.md").write_text("# 080 — Old\n\n**Created:** 2026-10-20 08:00\n", encoding="utf-8")
        (inbox / "093-U-checks.html").write_text("<title>093 — Manual checks</title>\n", encoding="utf-8")
        result = course(cwd, "status")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        for heading in ("## Done since 2026-10-22 10:00", "## In progress", "## Decisions", "## For you",
                        "## New in the inbox"):
            self.assertIn(heading, out)
        done = out.split("## Done since")[1].split("## In progress")[0]
        self.assertIn("Greeting", done)
        self.assertIn("plan 084", done)
        self.assertNotIn("Old", done)
        progress = out.split("## In progress")[1].split("## Decisions")[0]
        self.assertIn("loc-planning 087", progress)
        self.assertIn("plan 087", progress)
        decisions = out.split("## Decisions")[1].split("## For you")[0]
        self.assertIn("one cache module", decisions)
        self.assertIn("D-02", decisions)
        self.assertNotIn("D-01", decisions)
        self.assertIn("092-U-question-cache.md", out.split("## For you")[1].split("## New in the inbox")[0])
        self.assertIn("093-U-checks.html", out.split("## For you")[1].split("## New in the inbox")[0])
        new = out.split("## New in the inbox")[1]
        self.assertIn("091-stuck-greeting.md", new)
        self.assertNotIn("080-deferred-old.md", new)
        self.assertIn("**Last report to the user:** 2026-10-22 10:00", section(cwd))
        course(cwd, "status", "--mark")
        self.assertNotIn("**Last report to the user:** 2026-10-22 10:00", section(cwd))

    def test_status_without_a_course(self):
        cwd = project(self)
        result = course(cwd, "status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No course", result.stdout)


class CapTest(unittest.TestCase):
    def test_cap_is_the_agreed_items_plus_ten_unless_named(self):
        cwd = project(self)
        course(cwd, "start", "--limit", "none", "--agreed", "x")
        self.assertIn("**Steps:** 0 of 10", section(cwd))
        course(cwd, "stop", "--reason", "test")
        course(cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "plan 084", "--cap", "5")
        self.assertIn("**Steps:** 0 of 5", section(cwd))


class StopHookTest(unittest.TestCase):
    def test_open_course_blocks_and_an_executed_plan_counts_a_step(self):
        cwd = project(self)
        course(cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "plan 084", "--item", "plan 087")
        first = json.loads(course(cwd, "next", "--text", "loc-planning 084").stdout)
        self.assertEqual(first["banner"], "-------- starting: loc-planning 084 | plans 0 of 12 --------")
        self.assertIn("**Steps:** 0 of 12", section(cwd))
        second = json.loads(course(cwd, "next", "--text", "loc-orchestrate 084").stdout)
        self.assertEqual(second["banner"],
                         "-------- ended: loc-planning 084 | starting: loc-orchestrate 084 | plans 1 of 12 --------")
        self.assertIn("**Steps:** 1 of 12", section(cwd))
        for _ in range(3):
            result = stop_hook(cwd)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = json.loads(result.stdout)
            self.assertEqual(out["decision"], "block")
            self.assertIn("loc-orchestrate 084", out["reason"])
            self.assertIn("never ask", out["reason"])
        course(cwd, "next", "--text", "loc-orchestrate 084 (resumed)")
        course(cwd, "done", "--item", "plan 084")
        self.assertIn("**Next:** the first open item: plan 087", section(cwd),
                      "a finished step is never shown as next")
        self.assertIn("plan 087", json.loads(stop_hook(cwd).stdout)["reason"])
        third = json.loads(course(cwd, "next", "--text", "loc-planning 087").stdout)
        self.assertEqual(third["banner"],
                         "-------- ended: plan 084 | starting: loc-planning 087 | plans 1 of 12 --------")
        self.assertIn("**Steps:** 1 of 12", section(cwd))
        course(cwd, "next", "--text", "loc-orchestrate 087")
        self.assertIn("**Steps:** 2 of 12", section(cwd))

    def test_a_second_stop_after_the_hook_waits(self):
        cwd = project(self)
        course(cwd, "start", "--limit", "goal", "--agreed", "x", "--item", "plan 084")
        course(cwd, "next", "--text", "loc-orchestrate 084")
        result = stop_hook(cwd, active=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("**State:** open", section(cwd))
        self.assertIn("**Steps:** 1 of 11", section(cwd))

    def test_time_limit_stops_even_while_waiting(self):
        cwd = project(self)
        course(cwd, "start", "--limit", f"until {minutes(-5)}", "--agreed", "x", "--item", "plan 084")
        self.assertEqual(json.loads(stop_hook(cwd, active=True).stdout)["decision"], "block")
        self.assertIn("**State:** stopping — time limit", section(cwd))

    def test_time_limit_stops_after_one_report(self):
        cwd = project(self)
        course(cwd, "start", "--limit", f"until {minutes(-5)}", "--agreed", "x", "--item", "plan 084")
        first = json.loads(stop_hook(cwd).stdout)
        self.assertEqual(first["decision"], "block")
        self.assertIn("course.py stop", first["reason"])
        self.assertIn("**State:** stopping — time limit", section(cwd))
        second = stop_hook(cwd)
        self.assertEqual(second.stdout.strip(), "")
        self.assertRegex(section(cwd), r"\*\*State:\*\* closed .* — time limit")

    def test_future_time_limit_keeps_going(self):
        cwd = project(self)
        course(cwd, "start", "--limit", f"until {minutes(60)}", "--agreed", "x", "--item", "plan 084")
        self.assertEqual(json.loads(stop_hook(cwd).stdout)["decision"], "block")
        self.assertIn("**State:** open", section(cwd))

    def test_step_cap_stops(self):
        cwd = project(self)
        course(cwd, "start", "--limit", "none", "--agreed", "x", "--item", "plan 084")
        prd = cwd / "loc" / "PRD.md"
        prd.write_text(prd.read_text(encoding="utf-8").replace("**Steps:** 0 of 11", "**Steps:** 11 of 11"),
                       encoding="utf-8")
        self.assertEqual(json.loads(stop_hook(cwd).stdout)["decision"], "block")
        self.assertIn("**State:** stopping — step cap", section(cwd))
        self.assertEqual(stop_hook(cwd).stdout.strip(), "")

    def test_step_cap_lets_the_last_plan_finish(self):
        # `next` counts a plan when it starts, so the cap-th plan is still running at the cap.
        cwd = project(self)
        course(cwd, "start", "--limit", "none", "--agreed", "x", "--item", "plan 084")
        prd = cwd / "loc" / "PRD.md"
        prd.write_text(prd.read_text(encoding="utf-8").replace("**Steps:** 0 of 11", "**Steps:** 10 of 11"),
                       encoding="utf-8")
        course(cwd, "next", "--text", "loc-orchestrate 084")
        self.assertIn("**Steps:** 11 of 11", section(cwd))
        self.assertEqual(json.loads(stop_hook(cwd).stdout)["decision"], "block")
        self.assertIn("**State:** open", section(cwd))
        course(cwd, "done", "--item", "plan 084")
        stop_hook(cwd)
        self.assertIn("**State:** stopping — step cap", section(cwd))

    def test_nothing_to_do_without_an_open_course(self):
        for prd in (None, PRD, PRD + "\n## Course\n**State:** closed 2026-10-22 10:00 — done\n",
                    PRD + "\n## Course\nwhatever\n"):
            cwd = project(self, prd)
            result = stop_hook(cwd)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_registered_on_stop(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        commands = [h["command"] for group in hooks["Stop"] for h in group["hooks"]]
        self.assertTrue(any("hooks/director_stop.py" in c for c in commands), commands)


class SkillTest(unittest.TestCase):
    def test_skill_runs_the_course(self):
        skill = (ROOT / "skills" / "loc-director" / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("name: loc-director", "`banner`", "Never start without it", "One executed plan is one step", "`status`", "`stop`", "`pm`", "`architect`", "course.py start",
                       "course.py next", "--source", "goal", "none", "until", "masterskills:loc-planning",
                       "masterskills:loc-orchestrate"):
            self.assertIn(marker, skill)

    def test_skill_stops_and_reports(self):
        skill = (ROOT / "skills" / "loc-director" / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("inbox_owner.py --number", "--user", "Done:", "Skipped:", "Left:",
                       "/masterskills:loc-director", "should I continue", "never invent"):
            self.assertIn(marker, skill)

    def test_skill_starts_without_asking_when_told_to_work(self):
        skill = (ROOT / "skills" / "loc-director" / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("Calling you is the agreement", "without asking", "without limits", "none means `goal`"):
            self.assertIn(marker, skill)



class CourseNeverAsksTest(unittest.TestCase):
    def test_the_skills_a_course_runs_never_ask_to_continue(self):
        for name in ("loc-planning", "loc-orchestrate"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("In a `loc-director` course the director goes on: never ask to continue.", text, name)


if __name__ == "__main__":
    unittest.main()
