"""Tests for scripts/mutate.py: backup before a mutation, restore after it."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Scratch projects stay inside the repository (nothing is written outside it), in an ignored directory.
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MutateTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)
        self.app = self.project / "app.py"
        self.app.write_text('def greet(name):\n    return "Hello, " + name\n', encoding="utf-8")

    def run_mutate(self, *args: str) -> tuple:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "mutate.py"), *args], cwd=self.project,
                                capture_output=True, text=True, encoding="utf-8")
        return result.returncode, json.loads(result.stdout)

    def test_backup_mutate_restore(self):
        original = sha(self.app)
        self.assertEqual(self.run_mutate("backup", "app.py")[0], 0)
        self.app.write_text('def greet(name):\n    return "Bye"\n', encoding="utf-8")
        code, out = self.run_mutate("restore")
        self.assertEqual((code, out["restored"]), (0, "app.py"))
        self.assertEqual(sha(self.app), original)
        self.assertFalse((self.project / "loc" / "state" / "mutation.json").exists())
        self.assertFalse((self.project / "loc" / "state" / "mutation").exists())

    def test_second_backup_is_refused_and_keeps_the_first_copy(self):
        original = sha(self.app)
        self.run_mutate("backup", "app.py")
        self.app.write_text("broken\n", encoding="utf-8")
        code, out = self.run_mutate("backup", "app.py")
        self.assertEqual(code, 1)
        self.assertIn("still open", out["error"])
        self.run_mutate("restore")
        self.assertEqual(sha(self.app), original)

    def test_restore_without_entry_does_nothing(self):
        self.assertEqual(self.run_mutate("restore"), (0, {"restored": None}))

    def test_refuses_a_file_outside_the_project(self):
        code, out = self.run_mutate("backup", "../outside.py")
        self.assertEqual(code, 1)
        self.assertIn("not a file inside the project", out["error"])


if __name__ == "__main__":
    unittest.main()
