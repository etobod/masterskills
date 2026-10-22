#!/usr/bin/env python3
"""Stop hook: keep the director going while its course is open.

Reads loc/PRD.md `## Course` (`scripts/course.py`). While `**State:** open` and
neither the time limit (`until <time>`, checked here, not by the model) nor the
step cap is reached, it counts a step and blocks the end of the turn, naming
the next step. A reached limit sets `stopping — <reason>` and blocks once more
for the stop report; the next stop closes the course. Without a PRD, a course,
or an open one, it prints nothing: the turn ends as usual.

Reads the hook input JSON from stdin. Always exits 0.
"""

import datetime
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from course import STEPS, TIME, UNTIL, fields, join, now, set_field, split  # noqa: E402


def command(script: str) -> str:
    """How the model runs one of the plugin's scripts (as in session_start.py)."""
    root = (os.environ.get("CLAUDE_PLUGIN_ROOT") or str(PLUGIN_ROOT)).replace("\\", "/")
    python = os.environ.get("MASTERSKILLS_PYTHON")
    return f'{python} -B "{root}/{script}"' if python else f'sh "{root}/scripts/py.sh" {script}'


def decide(section: list):
    """(new section, reason to block or None)."""
    info = fields(section)
    state = info.get("State", "")
    if state.startswith("stopping"):
        reason = state.partition("—")[2].strip() or "limit"
        return set_field(section, "State", f"closed {now()} — {reason}"), None
    steps = STEPS.match(info.get("Steps", ""))
    if state != "open" or not steps:
        return section, None
    done, cap = int(steps[1]), int(steps[2])
    until = UNTIL.match(info.get("Limit", ""))
    limit = None
    if until and datetime.datetime.now() >= datetime.datetime.strptime(until[1], TIME):
        limit = "time limit"
    elif done >= cap:
        limit = "step cap"
    if limit:
        stop = command("scripts/course.py")
        return set_field(section, "State", f"stopping — {limit}"), (
            f"The course reached its {limit}. Finish no new task. Give the stop report (Done / Skipped / Left, "
            f'and the command to resume), then run `{stop} stop --reason "{limit}"`.')
    next_step = info.get("Next", "") or "the first open item"
    return set_field(section, "Steps", f"{done + 1} of {cap}"), (
        f"The director's course in loc/PRD.md is open (step {done + 1} of {cap}). Next: {next_step}. "
        "Carry on with loc-director: write each next step with course.py next before starting it, and never ask "
        "the user whether to continue. Stop only by the skill's stop rules, with course.py stop.")


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (ValueError, OSError):
        hook_input = {}
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_input.get("cwd") or os.getcwd())
    path = project / "loc" / "PRD.md"
    try:
        before, section, after = split(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return 0
    if section is None:
        return 0
    try:
        new, reason = decide(section)
    except ValueError:  # a course the hook cannot read switches it off
        return 0
    if new != section:
        path.write_text(join(before, new, after), encoding="utf-8")
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
