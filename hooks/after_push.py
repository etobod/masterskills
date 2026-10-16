#!/usr/bin/env python3
"""PostToolUse hook: after a successful `git push`, check CI once.

When the `Bash` command was a plain `git push ...` and the project has GitHub
Actions workflows (`.github/workflows/*.yml` or `*.yaml`), adds one instruction
to the context: run `gh run list` for the current branch once, record a failed
run as a `stuck` inbox file, and do not wait for a run in progress.

PostToolUse runs only after a tool call that succeeded, so a rejected push
adds nothing. Without workflows, on a detached HEAD or for any other command
the hook prints nothing.

Reads the hook input JSON from stdin. Always exits 0.
"""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_commands import plain  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
BRANCH = re.compile(r"[A-Za-z0-9._/-]+")


def branch(project: Path) -> str:
    try:
        result = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=project,
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    name = result.stdout.strip()
    if result.returncode != 0 or not BRANCH.fullmatch(name) or name.startswith("-"):
        return ""
    return name


def has_workflows(project: Path) -> bool:
    workflows = project / ".github" / "workflows"
    return any(workflows.glob("*.yml")) or any(workflows.glob("*.yaml"))


def script_command(root: str, script: str) -> str:
    """How the model runs one of the plugin's scripts. The OpenCode plugin names its
    Python in MASTERSKILLS_PYTHON: its shell may be PowerShell, which has no `sh`."""
    python = os.environ.get("MASTERSKILLS_PYTHON")
    return f'{python} -B "{root}/{script}"' if python else f'sh "{root}/scripts/py.sh" {script}'


def context(name: str) -> str:
    root = (os.environ.get("CLAUDE_PLUGIN_ROOT") or str(PLUGIN_ROOT)).replace("\\", "/")
    return (
        "## CI after push\n"
        "The push succeeded and the project runs GitHub Actions. Check CI once, "
        "with this command alone in the Bash tool:\n\n"
        f"gh run list --branch {name} --limit 1 --json status,conclusion,url\n\n"
        "- `conclusion: failure` → create an inbox file, add the run's `url` to it and tell the user "
        "in one sentence:\n"
        f'  `{script_command(root, "scripts/next_number.py")} --type stuck --slug "ci {name}" '
        f'--title "CI failed on {name}" --source "git push"`\n'
        "- `status: in_progress` or `queued` → one sentence to the user; do not wait or poll.\n"
        "- `success` → one sentence.\n"
        "- `gh` missing, not logged in or no access → say so in one sentence; no inbox file."
    )


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    command = (data.get("tool_input") or {}).get("command", "").strip()
    if data.get("tool_name") != "Bash" or not command or not plain(command):
        return 0
    try:
        words = shlex.split(command)
    except ValueError:
        return 0
    if words[:2] != ["git", "push"]:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    if not has_workflows(project):
        return 0
    name = branch(project)
    if name:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context(name),
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
