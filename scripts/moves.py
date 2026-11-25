#!/usr/bin/env python3
"""The moves of past divergent milestones, so a new variant does not repeat one.

  moves.py show [--last 12] [--file loc/moves.md]
      prints the last moves, newest first, one per line.
  moves.py add "<move>" [--plan <NNN>] [--file loc/moves.md]
      appends `- <date> (plan <NNN>): <move>`; the file is created from the template when missing.
  moves.py remove "<move>" [--file loc/moves.md]
      removes the last entry with that move (a variant the user did not pick).

A move is the means a variant used (e.g. "a name taken from the one verb the tool does"),
never the project's content.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "loc" / "moves.md"
ENTRY = re.compile(r"^- \S+ \(plan [^)]*\): (.+)$")


def norm(text: str) -> str:
    return " ".join(text.replace("|", "/").split()).lower()


def entries(path: Path) -> list:
    if not path.is_file():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)
    show = sub.add_parser("show")
    show.add_argument("--last", type=int, default=12)
    add = sub.add_parser("add")
    add.add_argument("move")
    add.add_argument("--plan", default="-")
    remove = sub.add_parser("remove")
    remove.add_argument("move")
    for command in (show, add, remove):
        command.add_argument("--file", type=Path, default=Path("loc/moves.md"))
    args = parser.parse_args()
    if args.action == "show":
        for line in list(reversed(entries(args.file)))[:max(args.last, 0)]:
            print(line)
        return 0
    move = " ".join(args.move.split())
    if not move:
        print(f"moves.py {args.action} needs the move, e.g. \"a name taken from the one verb the tool does\"")
        return 1
    if args.action == "remove":
        lines = args.file.read_text(encoding="utf-8").splitlines(keepends=True) if args.file.is_file() else []
        for i in range(len(lines) - 1, -1, -1):
            match = ENTRY.match(lines[i].rstrip("\n"))
            if match and norm(match.group(1)) == norm(move):
                args.file.write_text("".join(lines[:i] + lines[i + 1:]), encoding="utf-8")
                print(lines[i].strip())
                return 0
        print(f"no entry with the move \"{move}\" in {args.file.as_posix()}")
        return 1
    if not args.file.is_file():
        args.file.parent.mkdir(parents=True, exist_ok=True)
        args.file.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    text = args.file.read_text(encoding="utf-8")
    line = f"- {date.today().isoformat()} (plan {args.plan}): {move}\n"
    args.file.write_text(text + ("" if text.endswith("\n") else "\n") + line, encoding="utf-8")
    print(line.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
