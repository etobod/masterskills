#!/usr/bin/env python3
"""SessionStart hook: inject the core rules and the project's open inbox.

First it puts back a file left mutated by an interrupted session
(`scripts/mutate.py`), so broken code never survives into the next one.

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
from migrate import FORMAT, read_format  # noqa: E402
from mutate import restore  # noqa: E402


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def project_dir(hook_input: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_input.get("cwd") or os.getcwd())


def inbox_section(summary: dict) -> str:
    if not summary["has_inbox"]:
        return "## Inbox\nThis project has no `loc/inbox/` yet (`loc-init` sets it up)."

    lines = [f"## Inbox — {len(summary['inbox'])} open"]
    for item in summary["inbox"]:
        kind = item["type"] or "?"
        lines.append(f"- `{item['path']}` ({kind}) {item['title']}".rstrip())
    if not summary["inbox"]:
        lines.append("Nothing open.")
    if summary["state"]:
        lines.append(f"\nActive plan state: `{summary['state'][0]}`")
    lines.append(inbox_commands())
    return "\n".join(lines)


def script_command(root: str, script: str) -> str:
    """How the model runs one of the plugin's scripts. The OpenCode plugin names its
    Python in MASTERSKILLS_PYTHON: its shell may be PowerShell, which has no `sh`."""
    python = os.environ.get("MASTERSKILLS_PYTHON")
    return f'{python} -B "{root}/{script}"' if python else f'sh "{root}/scripts/py.sh" {script}'


def inbox_commands() -> str:
    # The root as Claude Code gave it, so plugin_commands.py recognises the command.
    root = (os.environ.get("CLAUDE_PLUGIN_ROOT") or str(PLUGIN_ROOT)).replace("\\", "/")
    return (
        "\nInbox commands: run each alone in the Bash tool, from the project directory "
        "(no `cd`, `&&` or PowerShell), so they need no approval.\n"
        f'- New file from its template, time from the clock: `{script_command(root, "scripts/next_number.py")} '
        '--type <question|deferred|...> --slug "<few words>" --title "<title>" --source "<where it came from>"`\n'
        "- Close a file: `mv loc/inbox/<file> loc/inbox/done/`"
    )


def mutation_section(project: Path) -> str:
    try:
        code, result = restore(project)
    except (OSError, ValueError, KeyError) as error:
        code, result = 2, {"error": str(error)}
    if code != 0:
        return f"\n\n## Interrupted mutation\nRestore failed: {result['error']} Fix this before anything else."
    if result["restored"]:
        return (f"\n\n## Interrupted mutation\nRestored `{result['restored']}` from its backup "
                "after an interrupted mutation; its hash matches the original.")
    return ""


def migration_section(project: Path) -> str:
    version = read_format(project / "loc")
    if version is None or version >= FORMAT:
        return ""
    return (f"\n\n## Old loc/ format\n`loc/` is in format {version}. Before other work, ask the user to run "
            f"/masterskills:loc-init to migrate loc/ to format {FORMAT}.")


def main() -> int:
    hook_input = read_input()
    project = project_dir(hook_input).resolve()
    mutation = mutation_section(project)
    rules = (PLUGIN_ROOT / "rules" / "core.md").read_text(encoding="utf-8").strip()
    summary = summarize(project)

    context = f"{rules}\n\n{inbox_section(summary)}{migration_section(project)}{mutation}\n"
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
