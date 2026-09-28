#!/usr/bin/env python3
"""Back up a production file before a hand-made mutation, and restore it after.

A test written after the code proves itself by failing on a deliberately broken
copy of the code. The mutation is made in place, so an interrupted session
could leave broken code behind; this script is the safety net:

    mutate.py backup <file>   -> copy to loc/state/mutacja/, entry in loc/state/mutacja.json
    mutate.py restore         -> copy back, check the hash, remove entry and copy

Only one mutation at a time: `backup` with an open entry is refused, never
overwritten. The SessionStart hook runs `restore` whenever an entry is left.
Never use `git checkout` for this: the file may hold uncommitted work.

Prints JSON. Exit 0 on success (also `restore` with nothing to restore),
1 when refused, 2 on a read or write error.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ENTRY = Path("loc/state/mutacja.json")
COPIES = Path("loc/state/mutacja")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup(project: Path, file: str) -> tuple:
    entry = project / ENTRY
    if entry.is_file():
        open_ = json.loads(entry.read_text(encoding="utf-8"))["file"]
        return 1, {"error": f"a mutation of {open_} is still open: run `restore` first"}
    path = (project / file).resolve()
    if not path.is_file() or not path.is_relative_to(project):
        return 1, {"error": f"{file}: not a file inside the project"}
    rel = path.relative_to(project).as_posix()
    copy = COPIES / rel
    (project / copy).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, project / copy)
    data = {"file": rel, "sha256": sha256(path), "copy": copy.as_posix()}
    entry.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0, {"backup": data}


def restore(project: Path) -> tuple:
    entry = project / ENTRY
    if not entry.is_file():
        return 0, {"restored": None}
    data = json.loads(entry.read_text(encoding="utf-8"))
    target, copy = project / data["file"], project / data["copy"]
    shutil.copy2(copy, target)
    if sha256(target) != data["sha256"]:
        return 2, {"error": f"{data['file']}: hash differs from the original after restore; "
                            f"the copy stays in {data['copy']}"}
    entry.unlink()
    shutil.rmtree(project / COPIES, ignore_errors=True)
    return 0, {"restored": data["file"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path("."), help="project root (default: .)")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("backup", help="copy a file before mutating it").add_argument("file")
    sub.add_parser("restore", help="put the original back")
    args = parser.parse_args()
    project = args.project.resolve()
    try:
        code, result = backup(project, args.file) if args.action == "backup" else restore(project)
    except (OSError, ValueError, KeyError) as error:
        code, result = 2, {"error": str(error)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
