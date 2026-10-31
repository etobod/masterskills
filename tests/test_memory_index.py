"""Tests for scripts/memory_index.py: the generated index of loc/MEMORY.md."""

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

JOURNAL = """# Dziennik

<!-- index:start -->
<!-- index:end -->

<!-- Entry format:
## 2026-01-15 14:30 — [Plan] Eksport do CSV
Up to 3 sentences. Details: loc/inbox/done/007-plan-csv-export.md
-->

## 2026-09-30 10:00 — [Plan] Najnowszy
Tekst. Details: loc/inbox/done/003-plan-c.md

## 2026-09-29 10:00 — [Plan] Checker komentarzy
Checker odrzuca każde <!-- poza znacznikami. Details: loc/inbox/done/002-plan-b.md

## 2026-09-28 10:00 — [Poprawka] Najstarszy
Tekst. Details: loc/inbox/done/001-plan-a.md
"""


class MemoryIndexTest(unittest.TestCase):
    def run_index(self, *args: str) -> dict:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "memory_index.py"),
                                 "--file", str(self.path), *args],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        self.path = project / "MEMORY.md"
        self.path.write_text(JOURNAL, encoding="utf-8")

    def rows(self) -> list:
        lines = self.path.read_text(encoding="utf-8").split("\n")
        return lines, [line for line in lines if line.startswith("| 20")]

    def test_comment_marker_inside_an_entry_does_not_hide_older_entries(self):
        out = self.run_index()
        self.assertEqual(out["entries"], 3)
        lines, rows = self.rows()
        self.assertEqual([row.split(" | ")[2] for row in rows], ["Najnowszy", "Checker komentarzy", "Najstarszy"])
        for row in rows:
            number = int(row.rstrip(" |").rsplit("| ", 1)[1])
            self.assertTrue(lines[number - 1].startswith("## 20"), row)
        self.assertFalse(any("Eksport do CSV" in row for row in rows))

    def test_second_run_changes_nothing(self):
        self.run_index()
        self.assertFalse(self.run_index()["changed"])

    def test_added_entry_of_type_planning(self):
        out = self.run_index("--type", "Planning", "--title", "Plan eksportu",
                             "--text", "Zaplanowano eksport. Details: loc/inbox/004-plan-d.md")
        self.assertEqual(out["entries"], 4)
        self.assertIn("[Planning] Plan eksportu", out["added"])


if __name__ == "__main__":
    unittest.main()
