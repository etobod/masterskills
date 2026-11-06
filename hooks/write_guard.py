#!/usr/bin/env python3
"""PreToolUse hook: files are written only inside the project.

`Write`, `Edit` and `NotebookEdit` with a path outside `$CLAUDE_PROJECT_DIR`
are denied: knowledge belongs in `loc/PATTERNS.md`, plans go through
`loc-planning`, scratch files go to the project's `loc/tmp/`. The only
exceptions are the directories in `permissions.additionalDirectories` of the
project's own `.claude/settings.json` and `.claude/settings.local.json`.

For `Bash` and `PowerShell` it is best effort: output redirections (`>`, `>>`,
`&>`, `>&file`), `tee` targets and the path of `Out-File`, `Set-Content`,
`Add-Content`, `New-Item` and `Tee-Object` are checked. Writes made by other
commands (`cp`, `mv`, a script, `python -c`), paths behind unknown variables
and relative paths after a `cd` are not detected.

Reads the hook input JSON from stdin. Prints a deny decision as JSON, or
nothing when the call is allowed. Always exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_commands import drive_path  # noqa: E402

REASON = (
    "masterskills: files are written only inside the project ({project}); "
    "refused: {path}. Put lessons in loc/PATTERNS.md, plans through loc-planning "
    "(loc/inbox/), and scratch files in the project's loc/tmp/."
)
DEVICES = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty", "nul", "con", "$null"}
OPERATORS = ";|&()\n"
VARIABLE = re.compile(r"\$(?:env:)?\{?(HOME|TMPDIR|TEMP|TMP|USERPROFILE)\}?(?![A-Za-z0-9_])", re.I)
PS_WRITERS = {"out-file", "set-content", "add-content", "new-item", "tee-object"}
PS_PATH_PARAMS = ("-filepath", "-path", "-literalpath")
PS_SWITCHES = {"-force", "-append", "-nonewline", "-noclobber", "-whatif", "-confirm", "-passthru"}


def tokens(command: str, escape: str = "\\") -> list:
    """Split a shell command into ('word' | 'op' | 'redirect', text) tokens.

    Quotes are removed from words; comments and here-document bodies are
    skipped. `escape` is `\\` for sh and the backtick for PowerShell.
    """
    out, word, heredocs = [], None, []
    i, n = 0, len(command)

    def add(text):
        nonlocal word
        word = (word or "") + text

    def flush(kind="word"):
        nonlocal word
        if word is not None:
            out.append((kind, word))
            word = None

    while i < n:
        c = command[i]
        if c in "'\"":
            end = i + 1
            while end < n and command[end] != c:
                end += 2 if c == '"' and command[end] == escape else 1
            add(command[i + 1:end])
            i = end + 1
        elif c == escape and i + 1 < n:
            add(command[i + 1])
            i += 2
        elif c == "#" and word is None:
            while i < n and command[i] != "\n":
                i += 1
        elif c == "\n" and heredocs:
            flush()
            out.append(("op", "\n"))
            i += 1
            for delimiter in heredocs:
                while i < n:
                    line_end = command.find("\n", i)
                    line_end = n if line_end < 0 else line_end
                    line = command[i:line_end].strip()
                    i = line_end + 1
                    if line == delimiter:
                        break
            heredocs = []
        elif command.startswith("<<", i) and escape == "\\":
            flush()
            i += 3 if command.startswith("<<-", i) else 2
            match = re.match(r"\s*(['\"]?)([\w.-]+)\1", command[i:])
            if match:
                heredocs.append(match.group(2))
                i += match.end()
        elif c == ">" or command.startswith("&>", i):
            if word is not None and (word.isdigit() or word == "*"):
                word = None  # `2>` or PowerShell `*>`: the stream, not a file
            flush()
            i += 1 if c == ">" else 2
            while i < n and command[i] in ">|":
                i += 1
            if i < n and command[i] == "&":
                i += 1
                if i < n and (command[i].isdigit() or command[i] == "-"):
                    i += 1  # `>&2`, `>&-`: a descriptor, not a file
                    continue
            while i < n and command[i] in " \t":
                i += 1
            while i < n and not command[i].isspace() and command[i] not in OPERATORS + "<>":
                if command[i] in "'\"":
                    end = command.find(command[i], i + 1)
                    end = n if end < 0 else end
                    add(command[i + 1:end])
                    i = end + 1
                else:
                    add(command[i])
                    i += 1
            flush("redirect")
        elif c.isspace():
            flush()
            i += 1
        elif c in OPERATORS:
            flush()
            out.append(("op", c))
            i += 1
        else:
            add(c)
            i += 1
    flush()
    return out


def command_targets(command: str, powershell: bool = False) -> list:
    """Paths that a shell command writes through redirections, `tee` or cmdlets."""
    targets, name, args = [], None, []

    def close():
        if name == "tee":
            targets.extend(a for a in args if not a.startswith("-"))
        elif name in PS_WRITERS:
            targets.extend(ps_path(args))

    for kind, text in tokens(command, "`" if powershell else "\\"):
        if kind == "redirect":
            targets.append(text)
        elif kind == "op":
            close()
            name, args = None, []
        elif name is None:
            name = os.path.basename(text).lower()
        else:
            args.append(text)
    close()
    return targets


def ps_path(args: list) -> list:
    """The target of a PowerShell writer cmdlet: its path parameter or first positional."""
    positional, i = [], 0
    while i < len(args):
        arg = args[i].lower()
        if arg.startswith("-") and any(p.startswith(arg) for p in PS_PATH_PARAMS) and len(arg) > 2:
            return args[i + 1:i + 2]
        if arg.startswith("-"):
            i += 1 if arg in PS_SWITCHES else 2
            continue
        positional.append(args[i])
        i += 1
    return positional[:1]


def resolve(path: str, cwd: Path) -> Path:
    path = VARIABLE.sub(lambda m: "~" if m.group(1).upper() in ("HOME", "USERPROFILE") else "/tmp", path)
    path = drive_path(path)
    candidate = Path(os.path.expanduser(path))
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return Path(os.path.normpath(candidate))


def inside(path: Path, project: Path) -> bool:
    try:
        path = path.resolve()
    except OSError:
        pass
    a, b = os.path.normcase(str(path)), os.path.normcase(str(project))
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def extra_dirs(project: Path) -> list:
    """The project's `permissions.additionalDirectories`, resolved; relative ones from the project."""
    dirs = []
    for name in ("settings.json", "settings.local.json"):
        try:
            data = json.loads((project / ".claude" / name).read_text(encoding="utf-8"))
            entries = data["permissions"]["additionalDirectories"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str) and entry.strip():
                path = Path(os.path.expanduser(os.path.expandvars(entry)))
                dirs.append((path if path.is_absolute() else project / path).resolve())
    return dirs


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()).resolve()
    cwd = Path(data.get("cwd") or project)
    tool, args = data.get("tool_name", ""), data.get("tool_input") or {}

    if tool in ("Bash", "PowerShell"):
        paths = [p for p in command_targets(args.get("command", ""), tool == "PowerShell")
                 if p.lower() not in DEVICES and "$" not in VARIABLE.sub("", p)]
    else:
        paths = [p for p in (args.get("file_path"), args.get("notebook_path")) if p]

    allowed = [project] + extra_dirs(project) if paths else []
    for path in paths:
        target = resolve(path, cwd)
        if not any(inside(target, root) for root in allowed):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON.format(project=project.as_posix(), path=path),
            }}))
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
