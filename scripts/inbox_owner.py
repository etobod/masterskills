#!/usr/bin/env python3
"""Hand an open inbox file to the user, or back, by renaming it.

A file that waits for the user carries `U` right after its number
(`091-U-stuck-x.md`); without it the file is the director's work. The name is
the only record of whose it is, so the file is found by its number alone and
renamed in `loc/inbox/`:

    inbox_owner.py --number 091 --user       091-stuck-x.md   -> 091-U-stuck-x.md
    inbox_owner.py --number 091 --director   091-U-stuck-x.md -> 091-stuck-x.md

Prints JSON `{"old", "new", "changed"}` (paths relative to the project). Exits 1
when no open file, or more than one, has that number.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

NAME = re.compile(r"^(\d{3,})-(?:U-)?(.+)$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)",
    )
    parser.add_argument("--number", required=True, help="the file's number, e.g. 091")
    owner = parser.add_mutually_exclusive_group(required=True)
    owner.add_argument("--user", action="store_true", help="the file waits for the user: add U")
    owner.add_argument("--director", action="store_true", help="the file is the director's work: drop U")
    args = parser.parse_args()

    if not args.number.isdigit():
        parser.error("--number takes digits, e.g. 091")
    inbox = args.project.resolve() / "loc" / "inbox"
    number = f"{int(args.number):03d}"
    found = sorted(inbox.glob(f"{number}-*.md")) if inbox.is_dir() else []
    if len(found) != 1:
        problem = "no open file" if not found else f"{len(found)} open files"
        print(json.dumps({"error": f"{problem} with number {number} in loc/inbox/"}))
        return 1
    old = found[0]
    rest = NAME.match(old.name).group(2)
    new = inbox / (f"{number}-U-{rest}" if args.user else f"{number}-{rest}")
    if new != old:
        old.rename(new)
    print(json.dumps({"old": f"loc/inbox/{old.name}", "new": f"loc/inbox/{new.name}", "changed": new != old}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
