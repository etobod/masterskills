#!/usr/bin/env python3
"""Check the project's frame: no goal, no work.

The frame is what every plan and review is weighed against:
  - `loc/PRD.md` `## Goal`, `## Core idea` and `## Scenarios`, each with more than the
    template's comments and placeholders (a missing heading counts as empty);
  - a test command in `CLAUDE.md` `## Commands` (a line naming `test` or `spec`).

Prints JSON `{"ok": bool, "missing": ["loc/PRD.md ## Goal", ...]}` and exits 1 when
something is missing. The missing parts are drafted and asked in the main session
(`skills/loc-init/references/frame.md`), never filled without the user.

Usage: frame.py [--project <dir>]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from init_project import PRD_FRAME, empty_sections  # noqa: E402

COMMENT = re.compile(r"<!--.*?-->", re.S)
TEST_NAME = re.compile(r"test|spec", re.I)
COMMANDS = re.compile(r"(?ms)^## Commands\s*?$(.*?)(?=^## |\Z)")


def has_test_command(project: Path) -> bool:
    """`CLAUDE.md` `## Commands` names a command that runs the tests."""
    try:
        text = (project / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    section = COMMANDS.search(text)
    body = COMMENT.sub("", section.group(1)) if section else ""
    return any(TEST_NAME.search(line) for line in body.splitlines())


def missing(project: Path) -> list:
    prd = project / "loc" / "PRD.md"
    if prd.is_file():
        gaps = [f"loc/PRD.md ## {name}" for name in empty_sections(prd, PRD_FRAME, missing_is_empty=True)]
    else:
        gaps = [f"loc/PRD.md ## {name}" for name in PRD_FRAME]
    if not has_test_command(project):
        gaps.append("CLAUDE.md ## Commands: test command")
    return gaps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    args = parser.parse_args()
    gaps = missing(args.project)
    print(json.dumps({"ok": not gaps, "missing": gaps}, indent=2))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
