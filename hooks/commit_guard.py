#!/usr/bin/env python3
"""PreToolUse hook: no AI attribution in commits.

Denies a `git commit`, run from `Bash` or `PowerShell`, whose command (or the
file given with `-F`/`--file`) carries an attribution marker: a
`Co-authored-by` naming Claude or Anthropic, "Generated with Claude Code", a
`claude.ai/code` link or `noreply@anthropic.com`. An ordinary mention of AI in the message, such as
`feat: add Claude API client`, passes.

Reads the hook input JSON from stdin. Prints a deny decision as JSON, or
nothing when the call is allowed. Always exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

COMMIT = re.compile(r"\bgit\b[^;&|\n]*?\bcommit\b")
MESSAGE_FILE = re.compile(r"(?:-F\s*|--file[=\s])\s*(\"[^\"]+\"|'[^']+'|\S+)")
MARKERS = [
    re.compile(r"co-authored-by:[^\n]*\b(claude|anthropic)\b[^\n\"']*", re.I),
    re.compile(r"generated (with|by) \W*claude code", re.I),
    re.compile(r"claude\.ai/code", re.I),
    re.compile(r"noreply@anthropic\.com", re.I),
]
REASON = (
    "masterskills: commits carry no AI attribution; remove this from the message and commit "
    "again: {marker}"
)


def message_files(command: str, cwd: Path) -> str:
    text = []
    for match in MESSAGE_FILE.finditer(command):
        path = Path(match.group(1).strip("'\""))
        try:
            text.append((path if path.is_absolute() else cwd / path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            pass
    return "\n".join(text)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if data.get("tool_name") not in ("Bash", "PowerShell") or not COMMIT.search(command):
        return 0

    cwd = Path(data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    text = command + "\n" + message_files(command, cwd)
    for marker in MARKERS:
        found = marker.search(text)
        if found:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON.format(marker=found.group(0)),
            }}))
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
