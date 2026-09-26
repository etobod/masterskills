#!/usr/bin/env python3
"""SessionStart hook: inject the core rules and the project's open inbox.

Runs on startup, /clear and after compaction, so the rules come back into
context whenever it is rebuilt. Reads the hook input JSON from stdin and
prints hookSpecificOutput.additionalContext as JSON.
"""

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from inbox_summary import summarize  # noqa: E402


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def project_dir(hook_input: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_input.get("cwd") or os.getcwd())


def inbox_section(summary: dict) -> str:
    if not summary["has_inbox"]:
        return "## Inbox\nThis project has no `inbox/` yet (`loc-init` sets it up)."

    lines = [f"## Inbox — {len(summary['inbox'])} open"]
    for item in summary["inbox"]:
        kind = item["type"] or "?"
        lines.append(f"- `{item['path']}` ({kind}) {item['title']}".rstrip())
    if not summary["inbox"]:
        lines.append("Nothing open.")
    if summary["state"]:
        lines.append(f"\nActive plan state: `{summary['state'][0]}`")
    return "\n".join(lines)


def main() -> int:
    hook_input = read_input()
    rules = (PLUGIN_ROOT / "rules" / "core.md").read_text(encoding="utf-8").strip()
    summary = summarize(project_dir(hook_input).resolve())

    context = f"{rules}\n\n{inbox_section(summary)}\n"
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    # ASCII-only JSON: safe whatever the console code page is on Windows.
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
