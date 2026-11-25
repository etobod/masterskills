#!/usr/bin/env python3
"""Say whether a finished plan changed the project's structure, so its diagrams need redrawing.

True when the plan added or deleted a code file, when it changed a file named on
a `**Sources:**` line of a diagram in `loc/diagrams/`, or when there is no
overview diagram yet. Otherwise false, with the reason. The plan's range runs
from `milestones[0].start` in the state file to a fresh snapshot (or `--to`);
`loc/` is left out. Documentation (`.md`, `.txt`, `.rst`) is not code.

    diagram_needed.py --state loc/state/<NNN>.json [--to <rev>]

Prints JSON {"needed", "reason", "files"}. Exit 0, or 2 when the state or git fails.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import git, snapshot  # noqa: E402

DOCS = {".md", ".txt", ".rst"}
SOURCES = re.compile(r"^\*\*Sources:\*\*\s*(.+)$", re.M)


def diagram_sources(project: Path) -> dict:
    """Each file named on a diagram's `**Sources:**` line, with the diagram that names it."""
    sources = {}
    for path in sorted((project / "loc" / "diagrams").glob("*.md")):
        for match in SOURCES.finditer(path.read_text(encoding="utf-8", errors="replace")):
            for item in match.group(1).split(","):
                name = item.strip().strip("`").split(":", 1)[0].strip()
                if name:
                    sources.setdefault(name, path.name)
    return sources


def decide(project: Path, changes: list) -> tuple:
    """(needed, reason, files) from (status, path) pairs of git --name-status."""
    if not (project / "loc" / "diagrams" / "overview.md").is_file():
        return True, "no overview diagram yet", []
    structural = [path for status, path in changes
                  if status[:1] in ("A", "D") and Path(path).suffix.lower() not in DOCS]
    if structural:
        return True, "code files added or deleted", structural
    sources = diagram_sources(project)
    named = [path for _, path in changes if path in sources]
    if named:
        diagrams = sorted({sources[path] for path in named})
        return True, f"files on a diagram's Sources line changed ({', '.join(diagrams)})", named
    return False, "no code file added or deleted, no diagram source changed", []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--state", type=Path, required=True, help="loc/state/<NNN>.json")
    parser.add_argument("--to", dest="end", help="end revision (default: a fresh snapshot)")
    args = parser.parse_args()
    project = args.project.resolve()
    state = args.state if args.state.is_absolute() else project / args.state
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
        start = (data.get("milestones") or [{}])[0].get("start")
        if not start:
            raise ValueError("milestones[0].start: no first snapshot in the state file")
        end = args.end or snapshot(project)
        lines = git(["diff", "--name-status", "--no-renames", start, end, "--", ".", ":!loc"], project).splitlines()
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    changes = [tuple(line.split("\t", 1)) for line in lines if "\t" in line]
    needed, reason, files = decide(project, changes)
    print(json.dumps({"needed": needed, "reason": reason, "files": files}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
