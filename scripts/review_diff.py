#!/usr/bin/env python3
"""Write the diff under review to a file and list the changed files.

`loc/` is left out: plans, reviews and questions are not the code under
review. Without `--to` the end point is a fresh snapshot of the working tree
(new files included, see snapshot.py), so uncommitted work is reviewed too.
`--from HEAD` in a repository with no commits starts from the empty tree.

    review_diff.py --from <rev> [--to <rev>] --out loc/review/018.diff [--paths a.py b/]

Prints JSON {"from", "to", "out", "files", "empty"}. Exit 0, or 2 when git fails.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import git, snapshot  # noqa: E402


def head_exists(project: Path) -> bool:
    try:
        return bool(git(["rev-parse", "--verify", "-q", "HEAD"], project))
    except RuntimeError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--from", dest="start", required=True, help="start revision or snapshot")
    parser.add_argument("--to", dest="end", help="end revision (default: a fresh snapshot)")
    parser.add_argument("--out", type=Path, required=True, help="diff file to write")
    parser.add_argument("--paths", nargs="*", default=[], help="limit the diff to these paths")
    args = parser.parse_args()

    project = args.project.resolve()
    out = args.out if args.out.is_absolute() else project / args.out
    try:
        end = args.end or snapshot(project)
        if args.start == "HEAD" and not head_exists(project):
            # No commits yet: everything in the project is the change.
            args.start = git(["hash-object", "-t", "tree", "--stdin"], project, stdin="")
        scope = ["--", *(args.paths or ["."]), ":!loc"]
        diff = git(["diff", args.start, end, *scope], project, strip=False)
        files = git(["diff", "--name-only", args.start, end, *scope], project).splitlines()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(diff.encode("utf-8"))
    except (RuntimeError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    print(json.dumps({"from": args.start, "to": end, "out": out.relative_to(project).as_posix()
                      if out.is_relative_to(project) else out.as_posix(),
                      "files": files, "empty": not files}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
