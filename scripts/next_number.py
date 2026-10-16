#!/usr/bin/env python3
"""Give the next inbox number, and optionally create the inbox file from its template.

The number is max(NNN in `loc/inbox/` and `loc/inbox/done/`) + 1, zero-padded to three
digits; an empty inbox gives `001`. Never count files by hand: counting gives
repeated numbers once files move to `loc/inbox/done/`.

With `--type`, `--slug` and `--title` the file `loc/inbox/NNN-<type>-<slug>.md` is
created from `templates/loc/inbox/<type>.md`, with the number, title, source and the
current time filled in. An existing file is never overwritten. `--what`, `--why` and
`--when` fill the sections of a `deferred` file in the same step, so it is never
left as the empty template; for a type without that section they are an error.

Prints JSON to stdout:
    {"number": "006", "now": "2026-01-15 14:30"}
    {"number": "006", "now": ..., "path": "loc/inbox/006-plan-csv-export.md", "created": true}
"""

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates" / "loc" / "inbox"
TYPES = ["brainstorm", "plan", "question", "deferred", "review", "stuck"]
NUMBER = re.compile(r"^(\d{3,})-")
SECTIONS = {"what": "What was deferred", "why": "Why not now", "when": "When to return"}


def fill(text: str, heading: str, value: str):
    """Replace the placeholder line under `## heading`; None when the template has no such section."""
    pattern = re.compile(rf"^(## {re.escape(heading)}\n)<[^\n]*>$", re.M)
    if not pattern.search(text):
        return None
    return pattern.sub(lambda m: m.group(1) + value.strip(), text, count=1)


def next_number(project: Path) -> str:
    numbers = [
        int(match.group(1))
        for folder in (project / "loc" / "inbox", project / "loc" / "inbox" / "done")
        if folder.is_dir()
        for path in folder.iterdir()
        if (match := NUMBER.match(path.name))
    ]
    return f"{max(numbers, default=0) + 1:03d}"


def slugify(text: str) -> str:
    text = text.replace("\u0142", "l").replace("\u0141", "L")  # NFKD leaves the Polish l-stroke
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50].rstrip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)",
    )
    parser.add_argument("--type", choices=TYPES, help="create a file of this type")
    parser.add_argument("--slug", help="short description for the file name")
    parser.add_argument("--title", help="title for the file header")
    parser.add_argument("--source", default="conversation", help="where it came from (Source)")
    for option, heading in SECTIONS.items():
        parser.add_argument(f"--{option}", help=f"text of the '{heading}' section")
    args = parser.parse_args()

    project = args.project.resolve()
    number = next_number(project)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    result = {"number": number, "now": now}

    if args.type:
        if not (args.slug and args.title):
            parser.error("--type needs --slug and --title")
        slug = slugify(args.slug)
        if not slug:
            parser.error("--slug has no usable characters")
        rel = f"loc/inbox/{number}-{args.type}-{slug}.md"
        path = project / rel
        if path.exists():
            print(json.dumps({**result, "path": rel, "created": False, "error": "exists"}))
            return 1
        text = (TEMPLATES / f"{args.type}.md").read_text(encoding="utf-8")
        for key, value in (("{NNN}", number), ("{TITLE}", args.title),
                           ("{DATE}", now), ("{SOURCE}", args.source)):
            text = text.replace(key, value)
        for option, heading in SECTIONS.items():
            value = getattr(args, option)
            if value:
                text = fill(text, heading, value)
                if text is None:
                    parser.error(f"--{option}: a {args.type} file has no '## {heading}' section")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        result.update(path=rel, created=True)

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
