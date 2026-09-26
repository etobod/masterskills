#!/usr/bin/env python3
"""Take a snapshot of the working tree without touching history, index or files.

A milestone's diff is `git diff <start> <end>` between two snapshots. The spec
names `git stash create`, but that ignores untracked files, so a milestone that
adds a file would show an empty diff. Instead the whole tree (tracked and new,
minus .gitignore) is added to a temporary index and stored with
`git commit-tree`: a dangling commit object, no ref, no branch, no stash entry.

    snapshot.py                                   -> {"hash": ...}
    snapshot.py --state tmp/state/018.json --milestone 2 --point start
        also writes the hash to milestones[1].start in the state file;
        with --point end the output adds the milestone's diff command and files.

Exit 0 on success, 2 when git fails or the state file cannot be updated.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def git(args: list, cwd: Path, env: dict = None, stdin: str = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, env=env, input=stdin,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def snapshot(project: Path) -> str:
    git_dir = Path(git(["rev-parse", "--absolute-git-dir"], project))
    handle, index = tempfile.mkstemp(prefix="masterskills-snapshot-", dir=git_dir)
    os.close(handle)
    os.unlink(index)  # git wants to create the index itself
    env = {**os.environ, "GIT_INDEX_FILE": index}
    try:
        try:
            head = git(["rev-parse", "--verify", "-q", "HEAD"], project)
        except RuntimeError:
            head = ""  # no commits yet
        if head:
            git(["read-tree", head], project, env)
        git(["add", "-A"], project, env)
        tree = git(["write-tree"], project, env)
        parents = ["-p", head] if head else []
        return git(["commit-tree", tree, *parents], project, env, stdin="masterskills snapshot\n")
    finally:
        if os.path.exists(index):
            os.unlink(index)


def record(state_path: Path, milestone: int, point: str, commit: str, project: Path) -> dict:
    data = json.loads(state_path.read_text(encoding="utf-8-sig"))
    item = data["milestones"][milestone - 1]
    item[point] = commit
    state_path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    extra = {}
    if point == "end" and item.get("start"):
        extra["diff"] = f"git diff {item['start']} {commit}"
        names = git(["diff", "--name-only", item["start"], commit], project)
        extra["files"] = names.splitlines()
    return extra


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--state", type=Path, help="state file to record the hash in")
    parser.add_argument("--milestone", type=int, help="1-based milestone number")
    parser.add_argument("--point", choices=["start", "end"])
    args = parser.parse_args()
    if args.state and not (args.milestone and args.point):
        parser.error("--state needs --milestone and --point")

    project = args.project.resolve()
    try:
        commit = snapshot(project)
        result = {"hash": commit}
        if args.state:
            state = args.state if args.state.is_absolute() else project / args.state
            result.update(record(state, args.milestone, args.point, commit, project))
    except (RuntimeError, OSError, ValueError, KeyError, IndexError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
