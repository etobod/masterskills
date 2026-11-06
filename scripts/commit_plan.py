#!/usr/bin/env python3
"""Commit what a plan changed, once, at the end of the plan. Never pushes.

The files are those changed between the plan's first snapshot
(`milestones[0].start` in the state file) and the working tree now, `loc/`
left out. Work the user had uncommitted before the plan and the plan did not
touch stays uncommitted. A file both the user and the plan changed is
committed whole. Git hooks run as usual; a commit they reject is an error.

A new top-level directory git tracks nothing in (e.g. `data/` written by a
manual check) is never committed by default: the run stops until each such
directory is named with `--add <dir>` (the plan's own work) or `--leave <dir>`
(left on disk, uncommitted, listed in `left`).

    commit_plan.py --state loc/state/018.json --message "feat(export): add CSV export"
    commit_plan.py --state loc/state/018.json --message "feat(kb): sources" --add src --leave data
    commit_plan.py --state loc/state/018.json --skip "CLAUDE.md: the user commits"

Records `commit` in the state file: the new hash (HEAD, with "already": true, when
the plan's changes were committed during the plan), "none" when the plan changed
no file outside `loc/`, or "skipped: <reason>".

Prints JSON {"ok", "commit", "files", "left"} or {"ok": false, "error"}.
Exit 0 on success, 1 for a rejected message or an undecided new directory, 2 when git or the state file fails.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import git, snapshot  # noqa: E402

CONVENTIONAL = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w./-]+\))?!?: \S")
AI_MENTION = re.compile(r"co-authored-by|\bclaude\b|anthropic|\bai\b|\bllm\b|generated (by|with)", re.IGNORECASE)


def record(state_path: Path, data: dict, value: str) -> None:
    data["commit"] = value
    state_path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def new_directories(files: list, project: Path) -> dict:
    """Top-level directory -> its changed files, for each directory git tracks no file in yet."""
    found = {}
    for name in files:
        top = name.split("/", 1)[0]
        if "/" in name and (top in found or not git(["ls-files", "--", top], project)):
            found.setdefault(top, []).append(name)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--state", type=Path, required=True, help="state file, e.g. loc/state/018.json")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--message", help="Conventional Commits message in English")
    group.add_argument("--skip", help="why the plan is not committed (the project's CLAUDE.md says so)")
    parser.add_argument("--add", action="append", default=[], metavar="DIR",
                        help="a new directory that is the plan's own work: commit it")
    parser.add_argument("--leave", action="append", default=[], metavar="DIR",
                        help="a new directory the plan did not make, e.g. manual-check data: do not commit it")
    args = parser.parse_args()

    project = args.project.resolve()
    state_path = args.state if args.state.is_absolute() else project / args.state
    try:
        data = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": f"state file: {error}"}))
        return 2

    if args.skip is not None:
        if not args.skip.strip():
            print(json.dumps({"ok": False, "error": "--skip needs a reason"}))
            return 1
        record(state_path, data, f"skipped: {args.skip.strip()}")
        print(json.dumps({"ok": True, "commit": data["commit"], "files": []}))
        return 0

    message = args.message.strip()
    if not CONVENTIONAL.match(message):
        print(json.dumps({"ok": False, "error": "the message must follow Conventional Commits, "
                          "e.g. 'feat(export): add CSV export'"}))
        return 1
    if AI_MENTION.search(message):
        print(json.dumps({"ok": False, "error": "the message must not mention AI, a model or Co-authored-by"}))
        return 1

    start = (data.get("milestones") or [{}])[0].get("start")
    if not start:
        print(json.dumps({"ok": False, "error": "milestones[0].start: no first snapshot in the state file"}))
        return 2
    try:
        # --no-renames: a renamed file lists its old path too, so its deletion is committed.
        files = git(["diff", "--name-only", "--no-renames", start, snapshot(project), "--", ".", ":!loc"],
                    project).splitlines()
        # A file untracked at the start and gone now (renamed or deleted) has nothing to commit.
        tracked = set(git(["ls-files", "--", *files], project).splitlines()) if files else set()
        files = [name for name in files if name in tracked or (project / name).exists()]
        new = new_directories(files, project)
        leave = {name.strip("/\\") for name in args.leave}
        undecided = sorted(set(new) - leave - {name.strip("/\\") for name in args.add})
        if undecided:
            listed = ", ".join(f"{name}/ ({len(new[name])} files)" for name in undecided)
            print(json.dumps({"ok": False, "error": (
                f"new directories git tracks nothing in: {listed}. Run again with --add <dir> for the plan's "
                "own work, --leave <dir> for files the plan did not make (e.g. data from a manual check)")}))
            return 1
        left = [name for top in sorted(new) if top in leave for name in new[top]]
        files = [name for name in files if name not in left]
        if not files:
            record(state_path, data, "none")
            print(json.dumps({"ok": True, "commit": "none", "files": [], "left": left}))
            return 0
        git(["add", "-A", "--", *files], project)
        if not git(["diff", "--cached", "--name-only", "--", *files], project).strip():
            # Already committed during the plan (e.g. by the user): record that commit, not "none".
            commit = git(["rev-parse", "HEAD"], project)
            record(state_path, data, commit)
            print(json.dumps({"ok": True, "commit": commit, "files": [], "left": left, "already": True}))
            return 0
        git(["commit", "-q", "-m", message, "--", *files], project)
        commit = git(["rev-parse", "HEAD"], project)
    except (RuntimeError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    record(state_path, data, commit)
    print(json.dumps({"ok": True, "commit": commit, "files": files, "left": left}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
