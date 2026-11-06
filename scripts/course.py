#!/usr/bin/env python3
"""The director's course: what the user agreed, kept in loc/PRD.md `## Course`.

The section holds only the current state, so a run cut by Esc or a crash
resumes from it:

    ## Course
    **State:** open | stopping — <reason> | closed <time> — <reason>
    **Agreed:** <time> — <the user's words>
    **Limit:** goal | none | until <YYYY-MM-DD HH:MM>
    **Steps:** <n> of <cap>   (plans executed: a new `loc-orchestrate <NNN>`)
    **Next:** <the next step, written before it starts; `done` sets it to the first open item>
    **Last report to the user:** <time>
    - [ ] plan 084 — agreed
    - [x] plan 091 — from loc/inbox/091-stuck-x.md (plan 084) — done <time>

Commands (times come from the clock, never from the model):

    start --limit <goal|none|"until YYYY-MM-DD HH:MM"> --agreed "<words>" [--item "<item>"]... [--cap <n>]
    next --text "<step>"            (prints a banner line; a new `loc-orchestrate <NNN>` counts a step)
    add --item "<item>" --source "<the file or plan it comes from>"
    done --item "<item>"
    stop --reason "<why>"
    status [--mark]

`status` prints Markdown in fixed sections built from the course, loc/MEMORY.md
and loc/inbox/ since the last report; `--mark` then moves the last report to now.
The other commands print JSON {"course": [<section lines>]}; `next` adds "banner". Exit 1 when the
course is missing, already open (start) or has no such item; 2 on a bad argument.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

CAP = 10  # plans beyond the agreed items
OPEN = "the first open item"
FIELD = re.compile(r"^\*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*?)\s*$")
UNTIL = re.compile(r"^until (\d{4}-\d{2}-\d{2} \d{2}:\d{2})$")
STEPS = re.compile(r"^(\d+) of (\d+)$")
PLAN = re.compile(r"loc-orchestrate\s+(\d+)")
ITEM = re.compile(r"^- \[(?P<mark>[ x])\] (?P<text>.+?)(?: — done (?P<done>\d{4}-\d{2}-\d{2} \d{2}:\d{2}))?$")
ENTRY = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) — \[([^\]]+)\] (.+?)\s*$")
RULING = re.compile(r"\(architect, (\d{4}-\d{2}-\d{2})\)")
DECISION = re.compile(r"^- (D-\d+):.*\((\d{4}-\d{2}-\d{2})\)\s*$")
CREATED = re.compile(r"^\*\*Created:\*\*\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", re.MULTILINE)
TIME = "%Y-%m-%d %H:%M"


def now() -> str:
    return datetime.datetime.now().strftime(TIME)


def split(text: str):
    """(before, section lines, after) of `## Course`; section is None when there is none."""
    lines = text.splitlines()
    for start, line in enumerate(lines):
        if line.strip() == "## Course":
            end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
            return lines[:start], lines[start + 1:end], lines[end:]
    return lines, None, []


def join(before: list, section: list, after: list) -> str:
    while before and not before[-1].strip():
        before = before[:-1]
    body = [*before, "", "## Course", *section]
    if after:
        body += ["", *after]
    return "\n".join(body).rstrip("\n") + "\n"


def fields(section) -> dict:
    found = {}
    for line in section or []:
        match = FIELD.match(line)
        if match:
            found[match["name"]] = match["value"]
    return found


def set_field(section: list, name: str, value: str) -> list:
    return [f"**{name}:** {value}" if (FIELD.match(line) and FIELD.match(line)["name"] == name) else line
            for line in section]


def is_open(section) -> bool:
    state = fields(section).get("State", "")
    return state == "open" or state.startswith("stopping")


def read(project: Path):
    path = project / "loc" / "PRD.md"
    return path, split(path.read_text(encoding="utf-8"))


def next_step(section: list, text: str) -> list:
    """Write the next step. A step of the cap is one plan executed: a `loc-orchestrate <NNN>` other than the
    current one. Planning, inbox files and agents are not counted, and resuming the same plan counts once."""
    info = fields(section)
    previous = info.get("Next", "")
    plan = PLAN.search(text)
    current = None if previous.startswith(OPEN) else PLAN.search(previous)
    steps = STEPS.match(info.get("Steps", ""))
    if plan and steps and not (current and current[1] == plan[1]):
        if int(steps[1]) >= int(steps[2]):
            # A plan started past the cap would be stopped by the Stop hook mid-run.
            print(json.dumps({"error": f"step cap reached ({steps[1]} of {steps[2]}): start no new plan, "
                                       "check the stop rules"}))
            return None
        section = set_field(section, "Steps", f"{int(steps[1]) + 1} of {steps[2]}")
    return set_field(section, "Next", text)


def banner(section: list, text: str, ended: str) -> str:
    """One line the user sees between two steps: what ended, what starts, the plans executed."""
    info = fields(section)
    if ended.startswith(OPEN):
        finished = [m for m in map(ITEM.match, section) if m and m["mark"] == "x" and m["done"]]
        ended = max(finished, key=lambda m: m["done"])["text"].split(" — ")[0] if finished else ""
    parts = [f"ended: {ended}"] if ended else []
    parts.append(f"starting: {text}")
    if STEPS.match(info.get("Steps", "")):
        parts.append(f"plans {info['Steps']}")
    return f"-------- {' | '.join(parts)} --------"


def check_limit(value: str) -> bool:
    if value in ("goal", "none"):
        return True
    match = UNTIL.match(value)
    if not match:
        return False
    try:
        datetime.datetime.strptime(match[1], TIME)
    except ValueError:
        return False
    return True


def start(project: Path, args) -> int:
    path, (before, section, after) = read(project)
    if is_open(section):
        print(json.dumps({"error": "a course is already open: stop it first"}))
        return 1
    stamp = now()
    new = ["**State:** open", f"**Agreed:** {stamp} — {args.agreed}", f"**Limit:** {args.limit}",
           f"**Steps:** 0 of {len(args.item) + CAP if args.cap is None else args.cap}", "**Next:** the first open item",
           f"**Last report to the user:** {stamp}", *[f"- [ ] {item} — agreed" for item in args.item]]
    path.write_text(join(before, new, after), encoding="utf-8")
    print(json.dumps({"course": new}))
    return 0


def change(project: Path, edit, extra=None) -> int:
    path, (before, section, after) = read(project)
    if not fields(section).get("State"):
        print(json.dumps({"error": "loc/PRD.md has no ## Course"}))
        return 1
    new = edit(section)
    if new is None:
        return 1
    path.write_text(join(before, new, after), encoding="utf-8")
    print(json.dumps({**(extra(section) if extra else {}), "course": new}))
    return 0


def add(section: list, item: str, source: str) -> list:
    return [*section, f"- [ ] {item} — from {source}"]


def done(section: list, item: str):
    for index, line in enumerate(section):
        match = ITEM.match(line)
        if match and match["mark"] == " " and (match["text"] == item or match["text"].startswith(f"{item} — ")):
            section = [*section[:index], f"- [x] {match['text']} — done {now()}", *section[index + 1:]]
            # The step that just ended is no longer next: a resumed session must not run it again.
            left = [m["text"] for m in map(ITEM.match, section) if m and m["mark"] == " "]
            return set_field(section, "Next", f"{OPEN}: {left[0]}" if left else OPEN)
    print(json.dumps({"error": f"no open item {item!r} in ## Course"}))
    return None


def since(value: str, last: str) -> bool:
    return value >= last


def status(project: Path, mark: bool) -> int:
    path = project / "loc" / "PRD.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    before, section, after = split(text)
    info = fields(section)
    if not info.get("State"):
        print("No course in loc/PRD.md: /masterskills:loc-director agrees one.")
        return 0
    last = info.get("Last report to the user", "")
    day = last[:10]
    out = [f"# Course — {info['State']}", f"Agreed: {info.get('Agreed', '')}",
           f"Limit: {info.get('Limit', '')} · steps {info.get('Steps', '')}", "", f"## Done since {last}"]

    items = [ITEM.match(line) for line in section]
    items = [m for m in items if m]
    out += [f"- {m['text']} ({m['done']})" for m in items if m["mark"] == "x" and m["done"] and since(m["done"], last)]
    memory = project / "loc" / "MEMORY.md"
    if memory.is_file():
        for line in memory.read_text(encoding="utf-8").splitlines():
            match = ENTRY.match(line)
            if match and since(match[1], last):
                out.append(f"- [{match[2]}] {match[3]} ({match[1]})")
    inbox = project / "loc" / "inbox"
    for file in sorted((inbox / "done").glob("*.md")):
        moved = datetime.datetime.fromtimestamp(file.stat().st_mtime).strftime(TIME)
        if since(moved, last):
            out.append(f"- closed `loc/inbox/done/{file.name}` ({moved})")

    out += ["", "## In progress", f"- Next: {info.get('Next', '')}"]
    out += [f"- [ ] {m['text']}" for m in items if m["mark"] == " "]

    out += ["", "## Decisions"]
    for line in text.splitlines():
        match = DECISION.match(line)
        if match and match[2] >= day:
            out.append(f"{line.strip()} (loc/PRD.md)")
    files = [path, *sorted(inbox.glob("*.md")), *sorted((inbox / "done").glob("*.md"))]
    for file in files:
        if not file.is_file():
            continue
        for line in file.read_text(encoding="utf-8").splitlines():
            match = RULING.search(line)
            if match and match[1] >= day and not DECISION.match(line):
                out.append(f"- {line.strip().lstrip('- ')} ({file.relative_to(project).as_posix()})")

    open_files = sorted([*inbox.glob("*.md"), *inbox.glob("*-checks.html")])
    out += ["", "## For you"]
    out += [f"- `loc/inbox/{f.name}`" for f in open_files if re.match(r"^\d{3,}-U-", f.name)]
    out += ["", "## New in the inbox"]
    for file in open_files:
        if re.match(r"^\d{3,}-U-", file.name):
            continue
        created = CREATED.search(file.read_text(encoding="utf-8"))
        if created and since(created[1], last):
            out.append(f"- `loc/inbox/{file.name}` ({created[1]})")
    # A heading followed by nothing gets "- none", so every section reads the same.
    shown = []
    for index, line in enumerate(out):
        shown.append(line)
        if line.startswith("## ") and (index + 1 == len(out) or not out[index + 1]):
            shown.append("- none")
    print("\n".join(shown))

    if mark:
        path.write_text(join(before, set_field(section, "Last report to the user", now()), after), encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
                        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    begin = commands.add_parser("start")
    begin.add_argument("--limit", required=True)
    begin.add_argument("--agreed", required=True)
    begin.add_argument("--item", action="append", default=[])
    begin.add_argument("--cap", type=int, help="plans to execute at most; default: the agreed items + 10")
    commands.add_parser("next").add_argument("--text", required=True)
    extra = commands.add_parser("add")
    extra.add_argument("--item", required=True)
    extra.add_argument("--source", required=True, help="the file or plan the item comes from; never your own idea")
    commands.add_parser("done").add_argument("--item", required=True)
    commands.add_parser("stop").add_argument("--reason", required=True)
    commands.add_parser("status").add_argument("--mark", action="store_true")
    for sub in commands.choices.values():
        sub.add_argument("--project", type=Path, default=argparse.SUPPRESS)
    args = parser.parse_args()
    project = args.project

    if args.command == "status":
        return status(project, args.mark)
    if not (project / "loc" / "PRD.md").is_file():
        print(json.dumps({"error": "no loc/PRD.md"}))
        return 1
    if args.command == "start":
        if not check_limit(args.limit):
            parser.error('--limit: goal, none or "until YYYY-MM-DD HH:MM"')
        return start(project, args)
    if args.command == "next":
        return change(project, lambda s: next_step(s, args.text), lambda s: {"banner": banner(next_step(s, args.text), args.text, fields(s).get("Next", ""))})
    if args.command == "add":
        return change(project, lambda s: add(s, args.item, args.source))
    if args.command == "done":
        return change(project, lambda s: done(s, args.item))
    return change(project, lambda s: set_field(s, "State", f"closed {now()} — {args.reason}"))


if __name__ == "__main__":
    sys.exit(main())
