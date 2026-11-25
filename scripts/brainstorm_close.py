#!/usr/bin/env python3
"""Mark a brainstorm's decisions as planned and close it once nothing is left.

`--covers B-01,B-03` appends `→ plan <NNN>` to each named decision of
`## Decisions`. A struck-through decision (`~~B-02 …~~`) does not count; one
marked `→ moved to …` (taken into the project by loc-init) is handled. When every
current decision is planned or moved and `## Open` holds nothing but the
template's placeholder, the status becomes `closed — planned in plan <NNN>, …`,
`## Resolution` names the plans and the file moves to `loc/inbox/done/`.
Otherwise it stays open and the JSON lists the decisions still unplanned.

A decision the brainstorm does not have is an error (exit 2): nothing is written.

Usage: brainstorm_close.py --brainstorm <NNN> --plan <NNN> --covers B-01,B-03 [--project <dir>]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

DECISION = re.compile(r"^- (~~)?(B-\d{2,})\b")
PLANNED = re.compile(r"→ plan (\d{3,})")
EMPTY = re.compile(r"<!--.*?-->|^\s*<[^\n]*>\s*$", re.S | re.M)


def find(project: Path, number: str):
    for path in sorted((project / "loc" / "inbox").glob(f"{number}-*brainstorm-*.md")):
        return path
    return None


def section(lines: list, name: str) -> tuple:
    """Start and end line index of `## <name>`'s body."""
    start = next((i + 1 for i, line in enumerate(lines) if line.strip() == f"## {name}"), None)
    if start is None:
        return None, None
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


def close(project: Path, brainstorm: str, plan: str, covers: list) -> tuple:
    path = find(project, brainstorm)
    if not path:
        return 2, {"ok": False, "error": f"no open brainstorm {brainstorm} in loc/inbox/"}
    lines = path.read_text(encoding="utf-8").split("\n")
    start, end = section(lines, "Decisions")
    if start is None:
        return 2, {"ok": False, "error": f"{path.name} has no ## Decisions"}
    current = {}
    for index in range(start, end):
        match = DECISION.match(lines[index])
        if match and not match.group(1):
            current[match.group(2)] = index
    unknown = [name for name in covers if name not in current]
    if unknown:
        return 2, {"ok": False, "error": f"not a current decision of {path.name}: {', '.join(unknown)}"}
    for name in covers:
        index = current[name]
        if f"→ plan {plan}" not in lines[index]:
            lines[index] = lines[index].rstrip() + f" → plan {plan}"
    unplanned = [name for name, index in current.items()
                 if not PLANNED.search(lines[index]) and "→ moved to" not in lines[index]]
    open_start, open_end = section(lines, "Open")
    still_open = open_start is not None and bool(EMPTY.sub("", "\n".join(lines[open_start:open_end])).strip())
    closed = not unplanned and not still_open
    if closed:
        plans = list(dict.fromkeys(number for index in current.values() for number in PLANNED.findall(lines[index])))
        names = ", ".join(f"plan {number}" for number in plans) or f"plan {plan}"
        lines = [re.sub(r"^\*\*Status:\*\*.*$", f"**Status:** closed — planned in {names}", line)
                 for line in lines]
        lines = [line for line in lines if not line.startswith("<!-- open while discussed")]
        res_start, res_end = section(lines, "Resolution")
        if res_start is not None and not EMPTY.sub("", "\n".join(lines[res_start:res_end])).strip():
            lines[res_start:res_end] = [f"Planned in {names}.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    result = {"ok": True, "brainstorm": path.relative_to(project).as_posix(), "closed": closed,
              "unplanned": unplanned, "open_items": still_open}
    if closed:
        done = project / "loc" / "inbox" / "done" / path.name
        done.parent.mkdir(parents=True, exist_ok=True)
        path.replace(done)
        result["brainstorm"] = done.relative_to(project).as_posix()
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brainstorm", required=True, help="the brainstorm's number, e.g. 004")
    parser.add_argument("--plan", required=True, help="the plan's number, e.g. 087")
    parser.add_argument("--covers", required=True, help="decisions the plan covers, e.g. B-01,B-03")
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    args = parser.parse_args()
    covers = [name.strip() for name in args.covers.split(",") if name.strip()]
    code, result = close(args.project, args.brainstorm.zfill(3), args.plan.zfill(3), covers)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
