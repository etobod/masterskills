"""plan_cost.py sums a plan's tokens per main session and agent type (B-17)."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scripts import ROOT, run, scratch_dir  # noqa: E402


def response(when: str, ident: str, tokens: int) -> str:
    usage = {"input_tokens": 2, "cache_creation_input_tokens": tokens - 12,
             "cache_read_input_tokens": 0, "output_tokens": 10}
    return json.dumps({"type": "assistant", "timestamp": when, "message": {"id": ident, "usage": usage}}) + "\n"


class PlanCostTest(unittest.TestCase):
    def setUp(self):
        self.project = scratch_dir(self)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        (self.project / "app.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)
        env = {**os.environ, "GIT_COMMITTER_DATE": "2026-11-20T10:00:00+00:00",
               "GIT_AUTHOR_DATE": "2026-11-20T10:00:00+00:00"}
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       cwd=self.project, check=True, env=env)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.project, capture_output=True,
                              text=True, check=True).stdout.strip()
        (self.project / "loc" / "state").mkdir(parents=True)
        (self.project / "loc" / "state" / "001.json").write_text(
            json.dumps({"milestones": [{"id": "M1", "start": head}]}), encoding="utf-8")
        self.logs = self.project / "logs"
        agents = self.logs / "session-a" / "subagents"
        agents.mkdir(parents=True)
        (self.logs / "session-a.jsonl").write_text(
            response("2026-11-19T09:00:00Z", "m0", 5000)        # before the plan: left out
            + response("2026-11-20T10:05:00Z", "m1", 300_000)
            + response("2026-11-20T10:05:00Z", "m1", 300_000)  # the same response logged twice
            + "not json\n", encoding="utf-8")
        (agents / "agent-1.jsonl").write_text(response("2026-11-20T11:00:00Z", "r1", 600_000), encoding="utf-8")
        (agents / "agent-1.meta.json").write_text(json.dumps({"agentType": "masterskills:rubber-duck"}),
                                                  encoding="utf-8")
        (agents / "agent-2.jsonl").write_text(response("2026-11-20T11:30:00Z", "j1", 100_000), encoding="utf-8")
        (agents / "agent-2.meta.json").write_text(json.dumps({"agentType": "masterskills:judge"}), encoding="utf-8")

    def cost(self, *extra: str) -> str:
        out = run("plan_cost.py", "--project", ".", "--state", "loc/state/001.json", *extra, cwd=self.project)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return out.stdout.strip()

    def test_tokens_per_session_and_agent_in_the_plan_window(self):
        self.assertEqual(self.cost("--logs", "logs", "--until", "2026-11-21T00:00:00Z"),
                         "1M tokens: rubber-duck 60%, main 30%, judge 10%")
        result = json.loads(self.cost("--logs", "logs", "--until", "2026-11-21T00:00:00Z", "--json"))
        self.assertEqual(result["by"], {"rubber-duck": 600_000, "main": 300_000, "judge": 100_000})

    def test_the_window_end_cuts_later_entries(self):
        self.assertEqual(self.cost("--logs", "logs", "--until", "2026-11-20T11:15:00Z"),
                         "900k tokens: rubber-duck 67%, main 33%")

    def test_no_logs_is_cost_unknown(self):
        self.assertEqual(self.cost("--logs", "missing"), "cost unknown")

    def test_the_journal_records_the_cost(self):
        text = (ROOT / "skills" / "loc-orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        journal = [line for line in text.splitlines() if line.startswith("5. **Journal.**")][0]
        self.assertIn("scripts/plan_cost.py --state loc/state/<NNN>.json", journal)
        self.assertIn("Cost: <its line>", journal)


if __name__ == "__main__":
    unittest.main()
