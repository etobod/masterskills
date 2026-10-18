#!/usr/bin/env python3
"""The queue of open plans, and making room in it for an urgent plan.

Open plans are `loc/inbox/NNN-plan-*.md` (never `loc/inbox/done/`). A plan named
`NNN-plan-<group>-<difficulty>-<topic>.md` runs in its group: a lower group runs
first, plans of one group change different files and run in any order. A plan
without a group (written before groups) comes first. Within a group, by number.

Without options, prints the queue:
    {"queue": [{"path", "number", "group", "running"}, ...]}

`--make-room G --keep NNN` raises by one the group of every open plan whose group is
G or higher, except plan NNN and a plan with a state file not yet `done` (it is
running). It renames the files with their new group and replaces each old file name
in the `.md` and `.json` files under `loc/` (not `loc/tmp/`), so no reference is left
pointing at a missing file. Prints {"queue": ..., "renamed": [[old, new], ...]}.

`--set NNN=G` (repeatable) gives plan NNN group G, whatever group it had (also a
plan written before groups), renaming files and references the same way. A running
plan is never renamed: it is listed in "skipped".
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PLAN = re.compile(r"^(?P<number>\d{3,})-plan-(?:(?P<group>\d+)-)?(?P<rest>.+\.md)$")


def running(project: Path) -> set:
    """Plan numbers with a state file whose phase is not `done`."""
    numbers = set()
    for path in (project / "loc" / "state").glob("*.json"):
        try:
            if json.loads(path.read_text(encoding="utf-8-sig")).get("phase") != "done":
                numbers.add(path.stem)
        except (OSError, ValueError):
            numbers.add(path.stem)  # unreadable: treat as running, never rename under it
    return numbers


def queue(project: Path) -> list:
    active = running(project)
    plans = []
    for path in (project / "loc" / "inbox").glob("*-plan-*.md"):
        match = PLAN.match(path.name)
        if match:
            group = match.group("group")
            plans.append({"path": f"loc/inbox/{path.name}", "number": match.group("number"),
                          "group": int(group) if group else None, "running": match.group("number") in active})
    return sorted(plans, key=lambda p: (p["group"] is not None, p["group"] or 0, p["number"]))


def regroup(project: Path, groups: dict) -> list:
    """Rename each plan of `groups` (number -> new group) and every reference to it."""
    renamed = []
    for plan in queue(project):
        if plan["number"] not in groups or plan["group"] == groups[plan["number"]]:
            continue
        old = Path(plan["path"]).name
        rest = PLAN.match(old).group("rest")
        new = f"{plan['number']}-plan-{groups[plan['number']]}-{rest}"
        (project / "loc" / "inbox" / old).rename(project / "loc" / "inbox" / new)
        renamed.append([old, new])
    replace_references(project, renamed)
    return renamed


def replace_references(project: Path, renamed: list) -> None:
    """Point every reference under `loc/` (not `loc/tmp/`) at the new file names."""
    if renamed:
        loc = project / "loc"
        for path in [*loc.rglob("*.md"), *loc.rglob("*.json")]:
            if (loc / "tmp") in path.parents:
                continue
            text = path.read_bytes().decode("utf-8")
            changed = text
            for old, new in renamed:
                changed = changed.replace(old, new)
            if changed != text:
                path.write_bytes(changed.encode("utf-8"))


def make_room(project: Path, first: int, keep: str) -> list:
    return regroup(project, {plan["number"]: plan["group"] + 1 for plan in queue(project)
                             if plan["group"] is not None and plan["group"] >= first
                             and not plan["running"] and plan["number"] != keep})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
                        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)")
    parser.add_argument("--make-room", type=int, metavar="G", help="raise by one every group from G up")
    parser.add_argument("--keep", metavar="NNN", help="the plan that takes group G and is not moved")
    parser.add_argument("--set", action="append", default=[], metavar="NNN=G", help="give plan NNN group G")
    args = parser.parse_args()
    project = args.project.resolve()
    result = {}
    if args.make_room is not None:
        if not args.keep:
            parser.error("--make-room needs --keep NNN")
        result["renamed"] = make_room(project, args.make_room, args.keep)
    if args.set:
        groups = {}
        for item in args.set:
            match = re.fullmatch(r"(\d{3,})=(\d+)", item)
            if not match:
                parser.error(f"--set {item}: expected NNN=G, e.g. 070=2")
            groups[match.group(1)] = int(match.group(2))
        active = {plan["number"] for plan in queue(project) if plan["running"]}
        result["skipped"] = sorted(number for number in groups if number in active)
        result["renamed"] = regroup(project, {n: g for n, g in groups.items() if n not in active})
    print(json.dumps({"queue": queue(project), **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
