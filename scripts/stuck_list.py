#!/usr/bin/env python3
"""The open stuck files as one list for the user, and their answers written back.

    stuck_list.py [--project <dir>]
        JSON {"items": [...], "text": "<the list to show>"}; each item has number, path,
        what (the first point that remains), triage (the architect's verdict),
        recommendation (`plan` or `let go`), ladder (`fresh`, `retry used` or
        `replanned as plan NNN`) and approved.
    stuck_list.py --approve NNN --words "<the user's words>"
        adds `**Approved by user:** <date> — <words>`: a new plan from it may be made.
    stuck_list.py --let-go NNN --words "<the user's words>"
        closes it: `## Resolution` says so, `**Status:** closed <date> — let go`,
        moved to loc/inbox/done/.

A stuck file never becomes a plan by itself: the first plan from the architect's
Triage `plan` needs no answer, any other needs `--approve` (course.py and
check_plan.py check it). Exit 1 when the file is not found, 2 on a bad argument.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

STUCK = re.compile(r"\b(\d{3,})-(?:U-)?stuck-[^\s`/\\)]+\.md\b")
REPLANNED = re.compile(r"^\*\*Replanned:\*\*\s*(\d{3,})", re.M)
APPROVED = re.compile(r"^\*\*Approved by user:\*\*\s*\S", re.M)
TRIAGE = re.compile(r"^\*\*Architect \(Triage\):\*\*\s*(.*)$", re.M)
STATUS = re.compile(r"^\*\*Status:\*\*.*$", re.M)


def today() -> str:
    return datetime.date.today().isoformat()


def find(project: Path, number: str, folders=("inbox", "inbox/done")):
    for folder in folders:
        for path in sorted((project / "loc" / folder).glob(f"{number}-*stuck-*.md")):
            return path
    return None


def verdict(text: str) -> str:
    """The architect's first Triage verdict word, `<…>` placeholders skipped."""
    for match in TRIAGE.finditer(text):
        value = match.group(1).strip().strip("*").lower()
        if value and not value.startswith("<"):
            return "let go" if value.startswith("let go") else value.split()[0].strip(":,.—")
    return ""


def remains(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() in ("### What remains", "**Remains:**"):
            for point in lines[index + 1:]:
                if point.startswith("#"):
                    break
                if point.strip().startswith("- "):
                    return point.strip()[2:].strip()
    return ""


def ladder(text: str) -> str:
    replanned = REPLANNED.search(text)
    if replanned:
        return f"replanned as plan {replanned.group(1)}"
    return "retry used" if "rounds 4–6" in text or "rounds 4-6" in text else "fresh"


def may_plan(text: str) -> bool:
    """The first plan from a Triage `plan` goes without asking; anything else needs the user's words."""
    return bool(APPROVED.search(text)) or (not REPLANNED.search(text) and verdict(text) in ("plan", "search"))


def item(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    title = re.match(r"#\s*\d+\s*[—-]\s*(.*)", text)
    triage = verdict(text)
    return {"number": path.name.split("-", 1)[0], "path": f"loc/inbox/{path.name}",
            "title": title.group(1).strip() if title else path.stem, "what": remains(text), "triage": triage,
            "recommendation": "let go" if triage == "let go" else "plan", "ladder": ladder(text),
            "approved": bool(APPROVED.search(text))}


def listing(project: Path) -> dict:
    items = [item(path) for path in sorted((project / "loc" / "inbox").glob("*-stuck-*.md"))]
    text = "\n".join(f"{index}. {entry['number']} — {entry['what'] or entry['title']} — architect: "
                     f"{entry['recommendation']} — {entry['ladder']}" + (" — approved" if entry["approved"] else "")
                     for index, entry in enumerate(items, 1))
    return {"items": items, "text": text or "No open stuck files."}


def approve(path: Path, words: str) -> None:
    text = path.read_text(encoding="utf-8")
    line = f"**Approved by user:** {today()} — {words}"
    status = STATUS.search(text)
    text = text[:status.end()] + "\n" + line + text[status.end():] if status else text.rstrip("\n") + "\n" + line + "\n"
    path.write_text(text, encoding="utf-8")


def let_go(project: Path, path: Path, words: str) -> Path:
    text = STATUS.sub(f"**Status:** closed {today()} — let go", path.read_text(encoding="utf-8"), count=1)
    note = f"Let go by the user {today()}: {words}"
    if "\n## Resolution" in text:
        head, tail = text.split("\n## Resolution", 1)
        rest = re.sub(r"^\n*(<[^>]*>\n?)?", "", tail)  # drop the template placeholder
        text = f"{head}\n## Resolution\n{note}\n{rest}"
    else:
        text = text.rstrip("\n") + f"\n\n## Resolution\n{note}\n"
    done = project / "loc" / "inbox" / "done" / path.name
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(text.rstrip("\n") + "\n", encoding="utf-8")
    path.unlink()
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--approve", metavar="NNN")
    action.add_argument("--let-go", metavar="NNN")
    parser.add_argument("--words", help="the user's words, required with --approve and --let-go")
    args = parser.parse_args()
    number = args.approve or args.let_go
    if not number:
        print(json.dumps(listing(args.project), indent=2, ensure_ascii=False))
        return 0
    if not args.words:
        parser.error("--words: the user's words are required")
    path = find(args.project, number, ("inbox",))
    if not path:
        print(json.dumps({"ok": False, "error": f"no open stuck file {number} in loc/inbox/"}))
        return 1
    if args.approve:
        approve(path, args.words)
        print(json.dumps({"ok": True, "approved": f"loc/inbox/{path.name}"}))
    else:
        done = let_go(args.project, path, args.words)
        print(json.dumps({"ok": True, "closed": done.relative_to(args.project).as_posix()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
