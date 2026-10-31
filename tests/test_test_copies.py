"""Tests for scripts/test_copies.py: a test that defines its own copy of the code it should test."""

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

FUNCTIONS = """function fft(input) {
  const N = input.length;
  if (N <= 1) return input.slice();
  return input.map((x, k) => x * k / N);
}
const getChainTip = (coeffs, t) => {
  let x = 0;
  for (const c of coeffs) x += c.amp * Math.cos(c.freq * t + c.phase);
  return x;
};
"""
PAGE = "<!doctype html>\n<canvas id=\"c\"></canvas>\n<script>\n" + FUNCTIONS + "</script>\n"
COPYING_TEST = ("import { test } from 'node:test';\n// copied from fourier.html for test independence\n"
                + FUNCTIONS + "test('fft', () => {});\n")
GREET = "def greet(name):\n    name = name.strip()\n    if not name:\n        name = 'you'\n    return 'Hi ' + name\n"


def run(project: Path) -> tuple:
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "test_copies.py")],
                            cwd=project, capture_output=True, text=True, encoding="utf-8")
    return result.returncode, json.loads(result.stdout)


class TestCopiesTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        # No `git init`: the script must work outside git.
        self.project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.project, True)

    def write(self, rel: str, text: str) -> None:
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_function_copied_from_a_page(self):
        self.write("fourier.html", PAGE)
        self.write("tests/fourier.test.js", COPYING_TEST)
        code, out = run(self.project)
        self.assertEqual(code, 0)
        found = {(c["name"], c["test"], c["test_line"], c["source"], c["source_line"]) for c in out["copies"]}
        self.assertEqual(found, {("fft", "tests/fourier.test.js", 3, "fourier.html", 4),
                                 ("getChainTip", "tests/fourier.test.js", 8, "fourier.html", 9)})

    def test_python_copy_and_import(self):
        self.write("app.py", GREET)
        self.write("tests/test_copy.py", GREET)
        self.write("tests/test_import.py", "from app import greet\n\ndef test_greet():\n    assert greet('A')\n")
        code, out = run(self.project)
        self.assertEqual([(c["name"], c["test"]) for c in out["copies"]], [("greet", "tests/test_copy.py")])

    def test_helpers_are_not_copies(self):
        """A helper that shares only a name with the code (a fixture factory) is not a copy."""
        self.write("app.py", "def save(db, row):\n    db.begin()\n    db.insert(row)\n    db.commit()\n"
                             "    return row.id\n")
        self.write("test_app.py", "from app import save\n\ndef make_name():\n    return 'A'\n\n"
                                  "def save(rows, row):\n    rows.append(row)\n    print(len(rows))\n"
                                  "    return len(rows)\n")
        code, out = run(self.project)
        self.assertEqual(out["copies"], [])


if __name__ == "__main__":
    unittest.main()
