"""ui_check.py: contrast, tokens, and (with Playwright) screenshots and page defects."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"
sys.path.insert(0, str(ROOT / "scripts"))
import ui_check  # noqa: E402

HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None

GOOD = """<!doctype html><html><head><meta name="viewport" content="width=device-width">
<style>body{margin:0;font:16px sans-serif;color:#111;background:#fff}main{max-width:40rem;padding:1rem}
a:focus-visible{outline:2px solid #0050d0}</style></head>
<body><main><h1>Title</h1><p>Readable text.</p><a href="#x">A link</a></main></body></html>"""

BAD = """<!doctype html><html><head><meta name="viewport" content="width=device-width">
<style>body{margin:0;font:16px sans-serif;background:#fff}
.wide{width:900px}.pale{color:#bbb}.box{width:60px;overflow:hidden;white-space:nowrap}
a{outline:none}</style></head>
<body><div class="wide">wide block</div><p class="pale">pale text</p><div class="box">a very long line of text</div>
<a href="#x">no focus</a></body></html>"""


class ContrastTest(unittest.TestCase):
    def test_wcag_ratios(self):
        self.assertAlmostEqual(ui_check.contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0, places=1)
        self.assertAlmostEqual(ui_check.contrast_ratio((118, 118, 118), (255, 255, 255)), 4.54, places=2)
        self.assertLess(ui_check.contrast_ratio((187, 187, 187), (255, 255, 255)), 4.5)

    def test_large_text_needs_less(self):
        self.assertEqual(ui_check.minimum_ratio(16, 400), 4.5)
        self.assertEqual(ui_check.minimum_ratio(24, 400), 3.0)
        self.assertEqual(ui_check.minimum_ratio(19, 700), 3.0)
        self.assertEqual(ui_check.minimum_ratio(19, 400), 4.5)


class ToolTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.dir = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "ui_check.py"), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_detect(self):
        out = json.loads(self.run_tool("--detect").stdout)
        self.assertEqual(out["playwright"], HAS_PLAYWRIGHT)
        self.assertIn("playwright install chromium", out["install"])

    def test_tokens_flag_raw_values_outside_the_tokens_file(self):
        tokens = self.dir / "tokens.css"
        tokens.write_text(":root{--ink:#111;--space-2:8px}\n", encoding="utf-8")
        css = self.dir / "app.css"
        css.write_text("/* #fff in a comment */\n.a{color:var(--ink);margin:0;border:1px solid var(--ink)}\n"
                       ".b{color:#ff0000}\n.c{padding:12px 0}\n.d{background:rgb(1,2,3)}\n.e{width:300px}\n",
                       encoding="utf-8")
        jsx = self.dir / "Card.jsx"
        jsx.write_text('const s = { fontSize: "14px", marginTop: 1 };\nexport const Card = () => <a href="#add">x</a>;\n',
                       encoding="utf-8")
        result = self.run_tool("--tokens", str(tokens), "--files", str(tokens), str(css), str(jsx))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        found = [(Path(d["file"]).name, d["line"], d["kind"]) for d in json.loads(result.stdout)["defects"]]
        self.assertEqual(found, [("app.css", 3, "raw-colour"), ("app.css", 4, "raw-size"),
                                 ("app.css", 5, "raw-colour"), ("Card.jsx", 1, "raw-size")])

    def test_clean_files_pass(self):
        tokens = self.dir / "tokens.css"
        tokens.write_text(":root{--ink:#111}\n", encoding="utf-8")
        css = self.dir / "app.css"
        css.write_text(".a{color:var(--ink);margin:0 1px}\n", encoding="utf-8")
        result = self.run_tool("--tokens", str(tokens), "--files", str(css))
        self.assertEqual(result.returncode, 0, result.stdout)

    @unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright is not installed: screenshots and page checks are skipped")
    def test_screenshots_and_a_clean_page(self):
        page = self.dir / "good.html"
        page.write_text(GOOD, encoding="utf-8")
        result = self.run_tool("--url", str(page), "--widths", "375,1024", "--out", str(self.dir / "shots"),
                               "--name", "good", "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual([Path(s).name for s in out["shots"]], ["good-375.png", "good-1024.png"])
        self.assertTrue((self.dir / "shots" / "good-375.png").stat().st_size > 0)

    @unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright is not installed: page checks are skipped")
    def test_page_defects(self):
        page = self.dir / "bad.html"
        page.write_text(BAD, encoding="utf-8")
        result = self.run_tool("--url", str(page), "--widths", "375", "--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        kinds = {(d["kind"], d["selector"]) for d in json.loads(result.stdout)["defects"]}
        for expected in (("horizontal-scroll", "html"), ("contrast", "p.pale"), ("cut-off", "div.box"), ("no-focus", "a")):
            self.assertIn(expected, kinds)

    @unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright is not installed: page checks are skipped")
    def test_links_with_one_class_are_all_walked_for_focus(self):
        # The walk stopped at the second `a.nav`, taking a repeated selector for a cycle.
        page = self.dir / "nav.html"
        page.write_text('<!doctype html><html><head><style>a.nav:focus{outline:2px solid #00f}'
                        'button{outline:none}</style></head><body><a class="nav" href="#1">One</a>'
                        '<a class="nav" href="#2">Two</a><button>Send</button></body></html>', encoding="utf-8")
        result = self.run_tool("--url", str(page), "--widths", "375", "--check")
        kinds = {(d["kind"], d["selector"]) for d in json.loads(result.stdout)["defects"]}
        self.assertIn(("no-focus", "button"), kinds, result.stdout)

    def test_an_address_that_cannot_open_is_a_json_error(self):
        result = self.run_tool("--url", "http://127.0.0.1:9/", "--widths", "375", "--check")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("error", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
