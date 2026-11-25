"""review_diff.py leaves generated and large files out of the review (B-15)."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scripts import ROOT, run, scratch_dir  # noqa: E402


class SkippedFilesTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)

    def write(self, rel: str, text: str) -> None:
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def review(self) -> tuple:
        out = run("review_diff.py", "--project", ".", "--from", "HEAD", "--out", "loc/review/x.diff",
                  cwd=self.project)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return json.loads(out.stdout), (self.project / "loc" / "review" / "x.diff").read_text(encoding="utf-8")

    def test_generated_and_large_files_are_named_but_not_diffed(self):
        # Lock files, minified, generated and large files cost review tokens and are not read (B-15).
        self.write("CLAUDE.md", "# P\n\n## Developer notes\nGenerated: `api/client_gen.py`, schema/\n\n## Limits\n")
        self.write("app.py", "print('hello')\n")
        self.write("package-lock.json", '{"lockfileVersion": 3}\n')
        self.write("static/app.min.js", "var a=1;\n")
        self.write("big.txt", "x" * 150 * 1024 + "\n")
        self.write("api/client_gen.py", "GENERATED = 1\n")
        self.write("schema/types.py", "TYPES = 1\n")
        self.write("vendor/out.js", "var out = 1;\n")
        self.write(".gitattributes", "vendor/out.js linguist-generated=true\n")
        result, diff = self.review()
        reasons = {item["file"]: item["reason"] for item in result["skipped"]}
        self.assertEqual(reasons, {"package-lock.json": "lock file", "static/app.min.js": "minified",
                                   "big.txt": "over 100 KB", "api/client_gen.py": "Generated: in CLAUDE.md",
                                   "schema/types.py": "Generated: in CLAUDE.md",
                                   "vendor/out.js": "linguist-generated"})
        self.assertIn("app.py", result["files"])
        for name in reasons:
            self.assertNotIn(name, result["files"])
            self.assertNotIn(f"+++ b/{name}", diff)
        self.assertIn("skipped: big.txt (150 KB, over 100 KB)", diff)
        self.assertIn("skipped: package-lock.json (", diff)
        self.assertIn("+print('hello')", diff)

    def test_a_plain_change_skips_nothing(self):
        self.write("app.py", "print('hello')\n")
        result, diff = self.review()
        self.assertEqual(result["skipped"], [])
        self.assertEqual(result["files"], ["app.py"])
        self.assertNotIn("skipped:", diff)

    def test_template_shows_a_generated_line(self):
        notes = (ROOT / "templates" / "CLAUDE.md").read_text(encoding="utf-8").split("## Developer notes", 1)[1]
        self.assertIn("Generated:", notes.split("\n## ", 1)[0])


if __name__ == "__main__":
    unittest.main()
