#!/usr/bin/env python3
"""PostToolUse hook: check a plan's state file right after it is written.

When `Write` or `Edit` touched `loc/state/<NNN>.json` of the project, runs the
same checks as `scripts/check_state.py` and, when the file is not valid JSON or
has problems, adds them to the context with an instruction to fix the file
before the next step. A valid file and every other path add nothing, so
`loc-orchestrate` does not run the validation command itself.

Reads the hook input JSON from stdin. Always exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_state import check  # noqa: E402

STATE = re.compile(r"^loc/state/\d{3,}\.json$")


def state_file(data: dict) -> Path | None:
    """The written path when it is a state file of the project, else None."""
    if data.get("tool_name") not in ("Write", "Edit"):
        return None
    raw = (data.get("tool_input") or {}).get("file_path")
    if not raw:
        return None
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()).resolve()
    path = Path(raw) if Path(raw).is_absolute() else project / raw
    try:
        rel = path.resolve().relative_to(project).as_posix()
    except ValueError:
        return None
    return path if STATE.match(rel) else None


def problems(path: Path) -> tuple:
    """(relative name, list of problems) for the state file."""
    name = f"loc/state/{path.name}"
    try:
        # utf-8-sig: some editors on Windows add a BOM to a perfectly valid file.
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError) as error:
        return name, [f"cannot be read: {error}"]
    except ValueError as error:
        return name, [f"not valid JSON: {error}"]
    return name, check(path, data)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    path = state_file(data)
    if path is None:
        return 0
    name, found = problems(path)
    if found:
        lines = "\n".join(f"- {p}" for p in found)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"## State file check\n`{name}` has problems:\n{lines}\n\n"
                                 "Fix the file before the next step; the check runs again after the write.",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
