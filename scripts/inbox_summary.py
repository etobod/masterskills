#!/usr/bin/env python3
"""List what the project has waiting: open inbox files and plan state files.

Open files are `inbox/*.md` (never `inbox/done/`), named `NNN-<type>-<desc>.md`.
State files are `tmp/state/*.json` of runs not yet done, newest first. A
project without `inbox/` gives an empty list, not an error.

Prints JSON to stdout:
    {"project": ..., "has_inbox": bool,
     "inbox": [{"path", "number", "type", "title"}], "state": [path, ...]}
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

NAME = re.compile(r"^(\d{3,})-([a-z]+)-")
TITLE = re.compile(r"^#\s+\d+\s*[—-]+\s*(.+?)\s*$")


def read_title(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    match = TITLE.match(line)
                    return match.group(1) if match else line.lstrip("# ").strip()
    except (OSError, UnicodeDecodeError):
        pass
    return ""


def finished(path: Path) -> bool:
    """A state file whose run ended stays as a record; it is not active."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")).get("phase") == "done"
    except (OSError, ValueError, AttributeError):
        return False


def summarize(project: Path) -> dict:
    inbox_dir = project / "inbox"
    inbox = []
    if inbox_dir.is_dir():
        for path in sorted(inbox_dir.glob("*.md")):
            match = NAME.match(path.name)
            inbox.append({
                "path": path.relative_to(project).as_posix(),
                "number": match.group(1) if match else None,
                "type": match.group(2) if match else None,
                "title": read_title(path),
            })

    state_dir = project / "tmp" / "state"
    state = []
    if state_dir.is_dir():
        files = sorted(state_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        state = [p.relative_to(project).as_posix() for p in files if not finished(p)]

    return {
        "project": project.as_posix(),
        "has_inbox": inbox_dir.is_dir(),
        "inbox": inbox,
        "state": state,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)",
    )
    args = parser.parse_args()
    print(json.dumps(summarize(args.project.resolve()), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
