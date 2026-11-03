"""Tests for scripts/search_log.py: the log of a search milestone decides keep, revert and stop."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "tmp" / "scratch" / "tests"


class SearchLogTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.dir = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.log = self.dir / "search-M2.md"

    def run_log(self, *args: str) -> tuple:
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "search_log.py"),
                                 "--log", str(self.log), *args],
                                capture_output=True, text=True, encoding="utf-8")
        out = result.stdout.strip()
        return result.returncode, (json.loads(out) if out.startswith("{") else out)

    def start(self, baseline="20%", target=">= 80", budget="5", give_up="3"):
        return self.run_log("--start", "--metric", "python score.py", "--baseline", baseline,
                            "--target", target, "--budget", budget, "--give-up", give_up)

    def add(self, score, hypothesis="idea", change="edit"):
        return self.run_log("--add", "--score", score, "--hypothesis", hypothesis, "--change", change)

    def test_better_score_is_kept_worse_reverted(self):
        self.start()
        code, out = self.add("30%")
        self.assertEqual((code, out["iteration"], out["keep"], out["best"], out["stop"]), (0, 1, True, 30, None))
        code, out = self.add("25")
        self.assertEqual((out["keep"], out["best"]), (False, 30))
        code, out = self.add("30")
        self.assertFalse(out["keep"], "an equal score is not a gain")

    def test_stops_at_target_never_past_it(self):
        self.start()
        code, out = self.add("85")
        self.assertEqual(out["stop"], "target")
        code, out = self.add("90")
        self.assertEqual(code, 1)
        self.assertIn("stopped", out["error"])

    def test_lower_is_better_target(self):
        self.start(baseline="0.9", target="<= 0.5")
        self.assertTrue(self.add("0.7")[1]["keep"])
        self.assertFalse(self.add("0.8")[1]["keep"])
        self.assertEqual(self.add("0.4")[1]["stop"], "target")

    def test_budget_and_give_up(self):
        self.start(budget="3", give_up="10")
        self.add("30")
        self.add("40")
        self.assertEqual(self.add("50")[1]["stop"], "budget")
        self.log.unlink()
        self.start(budget="10", give_up="2")
        self.add("10")
        self.assertEqual(self.add("15")[1]["stop"], "give-up")

    def test_baseline_meeting_target_stops_at_once(self):
        code, out = self.start(baseline="90")
        self.assertEqual(out["stop"], "target")

    def test_metric_change_resets_best_and_is_limited(self):
        self.start(give_up="10")
        self.add("40")
        code, out = self.run_log("--metric-change", "--reason", "case 17 had a wrong answer | fixed",
                                 "--baseline", "25", "--best", "35")
        self.assertEqual(code, 0)
        self.assertTrue(self.add("38")[1]["keep"], "best is the re-measured 35, not the old 40")
        self.run_log("--metric-change", "--reason", "second", "--baseline", "25", "--best", "38")
        code, out = self.run_log("--metric-change", "--reason", "third", "--baseline", "25", "--best", "38")
        self.assertEqual(code, 1)
        self.assertTrue(out["question"])

    def test_check_needs_a_stop(self):
        self.start()
        self.add("30")
        code, out = self.run_log("--check")
        self.assertEqual(code, 1)
        self.assertTrue(any("Stopped" in issue for issue in out["issues"]))
        self.run_log("--stop", "--reason", "no idea left after the prompt rewrite")
        self.assertEqual(self.run_log("--check"), (0, "ok"))
        self.assertIn("gave up: no idea left", self.log.read_text(encoding="utf-8"))

    def test_check_rejects_a_missing_or_broken_log(self):
        self.assertEqual(self.run_log("--check")[0], 1)
        self.log.write_text("# Search log\n\n**Target:** >= 80\n**Budget:** 1\n\n**Stopped:** budget\n",
                            encoding="utf-8")
        code, out = self.run_log("--check")
        self.assertEqual(code, 1)
        self.assertTrue(any("Metric" in issue for issue in out["issues"]))
        self.assertTrue(any("baseline" in issue for issue in out["issues"]))

    def test_start_refuses_an_existing_log_and_a_bad_target(self):
        self.start()
        self.assertEqual(self.start()[0], 1)
        self.log.unlink()
        self.assertEqual(self.start(target="80")[0], 1)


if __name__ == "__main__":
    unittest.main()
