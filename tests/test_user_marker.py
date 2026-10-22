"""The `U` marker: an inbox file that waits for the user carries `U` right after its number."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def project(test: unittest.TestCase) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=SCRATCH))
    test.addCleanup(shutil.rmtree, path, True)
    (path / "loc" / "inbox" / "done").mkdir(parents=True)
    return path


def run(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, "-B", str(ROOT / script), *args], capture_output=True,
                          text=True, encoding="utf-8", cwd=cwd, env=env)


def create(cwd: Path, kind: str, *extra: str) -> subprocess.CompletedProcess:
    return run("scripts/next_number.py", "--project", str(cwd), "--type", kind, "--slug", "x", "--title", "X",
               "--by", "test", *extra, cwd=cwd)


class NextNumberTest(unittest.TestCase):
    def test_question_and_brainstorm_wait_for_the_user(self):
        cwd = project(self)
        self.assertEqual(json.loads(create(cwd, "question").stdout)["path"], "loc/inbox/001-U-question-x.md")
        self.assertEqual(json.loads(create(cwd, "brainstorm").stdout)["path"], "loc/inbox/002-U-brainstorm-x.md")
        self.assertEqual(json.loads(create(cwd, "deferred").stdout)["path"], "loc/inbox/003-deferred-x.md")
        self.assertEqual(json.loads(create(cwd, "plan").stdout)["path"], "loc/inbox/004-plan-x.md")

    def test_user_flag_marks_other_types(self):
        cwd = project(self)
        for number, kind in enumerate(("deferred", "review", "stuck"), 1):
            out = json.loads(create(cwd, kind, "--user").stdout)
            self.assertEqual(out["path"], f"loc/inbox/{number:03d}-U-{kind}-x.md")
        result = create(cwd, "plan", "--user")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(run("scripts/next_number.py", "--project", str(cwd), cwd=cwd).stdout)["number"],
                         "004")


class OwnerTest(unittest.TestCase):
    def test_rename_by_number(self):
        cwd = project(self)
        (cwd / "loc" / "inbox" / "091-stuck-x.md").write_text("# 091\n", encoding="utf-8")
        result = run("scripts/inbox_owner.py", "--project", str(cwd), "--number", "091", "--user", cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["new"], "loc/inbox/091-U-stuck-x.md")
        self.assertTrue((cwd / "loc" / "inbox" / "091-U-stuck-x.md").is_file())
        result = run("scripts/inbox_owner.py", "--project", str(cwd), "--number", "91", "--director", cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((cwd / "loc" / "inbox" / "091-stuck-x.md").is_file())
        result = run("scripts/inbox_owner.py", "--project", str(cwd), "--number", "091", "--director", cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["changed"])

    def test_missing_file_fails(self):
        cwd = project(self)
        result = run("scripts/inbox_owner.py", "--project", str(cwd), "--number", "092", "--user", cwd=cwd)
        self.assertEqual(result.returncode, 1)


class SummaryTest(unittest.TestCase):
    def test_user_files_come_first(self):
        cwd = project(self)
        (cwd / "loc" / "inbox" / "001-deferred-a.md").write_text("# 001 — A\n", encoding="utf-8")
        (cwd / "loc" / "inbox" / "002-U-question-b.md").write_text("# 002 — B\n", encoding="utf-8")
        summary = json.loads(run("scripts/inbox_summary.py", "--project", str(cwd), cwd=cwd).stdout)
        items = {item["number"]: item for item in summary["inbox"]}
        self.assertEqual((items["001"]["type"], items["001"]["user"]), ("deferred", False))
        self.assertEqual((items["002"]["type"], items["002"]["user"]), ("question", True))
        hook = subprocess.run([sys.executable, "-B", str(ROOT / "hooks" / "session_start.py")],
                              input=json.dumps({"cwd": str(cwd)}), capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "CLAUDE_PROJECT_DIR": str(cwd)})
        text = json.loads(hook.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLess(text.index("002-U-question-b.md"), text.index("001-deferred-a.md"))
        self.assertIn("waits for you", text.split("002-U-question-b.md")[1].splitlines()[0])


class RuleTest(unittest.TestCase):
    def test_rule_three_names_the_marker(self):
        rule = (ROOT / "rules" / "core.md").read_text(encoding="utf-8").split("3. ")[1].split("\n4. ")[0]
        self.assertIn("open work", rule)
        self.assertIn("`U`", rule)

    def test_state_accepts_a_user_stuck_file(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        self.addCleanup(sys.path.remove, str(ROOT / "scripts"))
        import check_state
        self.assertTrue(check_state.STUCK.match("loc/inbox/091-U-stuck-x.md"))


if __name__ == "__main__":
    unittest.main()
