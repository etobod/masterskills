#!/usr/bin/env python3
"""Keep `loc/MEMORY.md` in order: entries newest first, a generated index, trimmed to N.

An entry is a level-2 heading and the text under it:

    ## 2026-01-15 14:30 — [Plan] CSV export
    Up to 3 sentences. Details: loc/inbox/done/007-plan-csv-export.md

The index is a table (date, type, topic, line of the entry) rewritten between
`<!-- index:start -->` and `<!-- index:end -->`; never edit it by hand. Only the
newest `--keep` entries stay (default 1000). Running it twice changes nothing.

With `--type`, `--title` and `--text` it first adds an entry stamped with the
current time, so the time never comes from memory.

Prints JSON {"file", "entries", "trimmed", "changed", "added"?}. Exit 0, or 2
when the file or its index markers are missing.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

START, END = "<!-- index:start -->", "<!-- index:end -->"
ENTRY = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) — \[([^\]]+)\] (.+?)\s*$")
TYPES = ["Plan", "Planning", "Review", "Fix", "Decision"]


def split_entries(lines: list) -> tuple:
    """Split the part after the index into (preamble, [entry lines, ...])."""
    preamble, entries, in_comment = [], [], False
    for line in lines:
        if not in_comment and ENTRY.match(line):
            entries.append([line])
            continue
        # An example entry inside an HTML comment is not an entry. Only a line that
        # starts with `<!--` opens a comment: an entry's text may mention the marker.
        if line.lstrip().startswith("<!--") and "-->" not in line.split("<!--", 1)[1]:
            in_comment = True
        elif "-->" in line:
            in_comment = False
        (entries[-1] if entries else preamble).append(line)
    return preamble, entries


def clean(entry: list) -> list:
    while len(entry) > 1 and not entry[-1].strip():
        entry = entry[:-1]
    return entry


def build(head: list, preamble: list, entries: list) -> str:
    while preamble and not preamble[-1].strip():
        preamble = preamble[:-1]
    while preamble and not preamble[0].strip():
        preamble = preamble[1:]
    # The index has a fixed number of lines, so each entry's line is known before it is written.
    index_lines = len(entries) + 2 if entries else 0
    out = head + [START] + [""] * index_lines + [END] + ([""] + preamble if preamble else [])
    rows = ["| Date | Type | Topic | Line |", "|---|---|---|---|"] if entries else []
    for entry in entries:
        out.append("")
        date, kind, title = ENTRY.match(entry[0]).groups()
        rows.append(f"| {date} | {kind} | {title.replace('|', '/')} | {len(out) + 1} |")
        out += entry
    first = len(head) + 1
    out[first:first + index_lines] = rows
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--file", type=Path, help="default: <project>/loc/MEMORY.md")
    parser.add_argument("--keep", type=int, default=1000, help="entries to keep (default 1000)")
    parser.add_argument("--type", choices=TYPES, help="add an entry of this type first")
    parser.add_argument("--title", help="entry title")
    parser.add_argument("--text", help="entry text: up to 3 sentences and the loc/inbox/done/ link")
    args = parser.parse_args()
    if args.type and not (args.title and args.text):
        parser.error("--type needs --title and --text")
    if args.keep < 1:
        parser.error("--keep must be at least 1")

    path = args.file or args.project / "loc" / "MEMORY.md"
    try:
        original = path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        print(json.dumps({"file": path.as_posix(), "error": str(error)}))
        return 2
    newline = "\r\n" if "\r\n" in original else "\n"
    lines = original.replace("\r\n", "\n").split("\n")
    if START not in lines or END not in lines or lines.index(START) > lines.index(END):
        print(json.dumps({"file": path.as_posix(), "error": f"missing {START} / {END} lines"}))
        return 2

    head, rest = lines[:lines.index(START)], lines[lines.index(END) + 1:]
    preamble, entries = split_entries(rest)
    result = {"file": path.as_posix()}
    if args.type:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        heading = f"## {now} — [{args.type}] {' '.join(args.title.split())}"
        entries.append([heading, args.text.strip()])
        result["added"] = heading[3:]

    # Newest first; the sort is stable, so entries with the same minute keep their order.
    entries = sorted((clean(e) for e in entries), key=lambda e: ENTRY.match(e[0]).group(1), reverse=True)
    result["trimmed"] = max(0, len(entries) - args.keep)
    entries = entries[:args.keep]

    text = build(head, preamble, entries).replace("\n", newline)
    changed = text != original
    if changed:
        path.write_bytes(text.encode("utf-8"))
    result.update(entries=len(entries), changed=changed)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
