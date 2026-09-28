#!/usr/bin/env python3
"""PreToolUse hook: the skills' own commands run without a permission prompt.

Allows exactly these `Bash` commands, each run on its own:

- `sh "<plugin root>/scripts/py.sh" scripts/<name>.py ...`, where
  `scripts/<name>.py` is one of the plugin's scripts;
- `date +<format>`;
- `mv` or `git mv` of one file from `loc/inbox/` to `loc/inbox/done/`;
- `gh run list --branch <branch> --limit 1 --json status,conclusion,url`, the
  CI check that `after_push.py` asks for.

Anything with a shell operator, substitution or redirection outside quotes
(`;`, `&`, `|`, `<`, `>`, `$`, backtick, parentheses, newline, glob), or with `$` or
a backtick inside double quotes, is left to the normal permission rules. A skill's `allowed-tools` is not used for this: when the model starts a
skill with the Skill tool, those rules can reach the permission check after the
skill's first command.

Reads the hook input JSON from stdin. Prints an allow decision as JSON, or
nothing. Always exits 0.
"""

import json
import os
import re
import shlex
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
# The skills show the model the root as Claude Code gave it, which may differ
# from the resolved path (a symlink, another spelling of the drive).
ROOTS = [PLUGIN_ROOT] + ([Path(os.environ["CLAUDE_PLUGIN_ROOT"])] if os.environ.get("CLAUDE_PLUGIN_ROOT") else [])
OPERATORS = set(";&|<>()$`\n\r*?[{")  # outside quotes; the last four expand to file names
INBOX_FILE = re.compile(r"loc/inbox/[^/\\]+")
DONE_FILE = re.compile(r"loc/inbox/done/[^/\\]*")
BRANCH = re.compile(r"[A-Za-z0-9._/][A-Za-z0-9._/-]*")
REASON = "masterskills: the plugin's own command"


def plain(command: str) -> bool:
    """True when the command is one simple command: no operator, substitution
    or redirection outside quotes, and no `$` or backtick inside double quotes.
    """
    quote, i = None, 0
    while i < len(command):
        c = command[i]
        if quote == "'":
            quote = None if c == "'" else quote
        elif c == "\\":
            i += 1  # the next character is literal
        elif quote == '"':
            if c in "$`":
                return False
            quote = None if c == '"' else quote
        elif c in "'\"":
            quote = c
        elif c in OPERATORS:
            return False
        i += 1
    return quote is None


def same_path(given: str, expected: Path) -> bool:
    given = given.replace("\\", "/")
    if os.name == "nt" and re.match(r"^/[a-zA-Z]/", given):
        given = f"{given[1]}:{given[2:]}"
    return os.path.normcase(os.path.normpath(given)) == os.path.normcase(os.path.normpath(expected))


def allowed(words: list) -> bool:
    if len(words) >= 3 and words[0] == "sh" and any(same_path(words[1], root / "scripts" / "py.sh")
                                                    for root in ROOTS):
        script = words[2]
        return (re.fullmatch(r"scripts/[A-Za-z0-9_]+\.py", script) is not None
                and (PLUGIN_ROOT / script).is_file())
    if words[:3] == ["gh", "run", "list"]:
        return (len(words) == 9 and words[3] == "--branch" and BRANCH.fullmatch(words[4]) is not None
                and words[5:] == ["--limit", "1", "--json", "status,conclusion,url"])
    if words[0] == "date":
        return len(words) > 1 and all(word.startswith("+") for word in words[1:])
    move = words[2:] if words[:2] == ["git", "mv"] else words[1:] if words[0] == "mv" else None
    if move is None or len(move) != 2 or any(".." in path for path in move):
        return False
    return INBOX_FILE.fullmatch(move[0]) is not None and DONE_FILE.fullmatch(move[1]) is not None


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
    if words and allowed(words):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": REASON,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
