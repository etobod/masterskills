#!/usr/bin/env python3
"""Write the diff under review to a file and list the changed files.

`loc/` is left out: plans, reviews and questions are not the code under
review. Without `--to` the end point is a fresh snapshot of the working tree
(new files included, see snapshot.py), so uncommitted work is reviewed too.
`--from HEAD` in a repository with no commits, and `--from empty` always, start
from the empty tree: the whole project is the change. `--exclude` leaves paths out.

Files nobody reviews by reading are left out of the diff and of `files`: lock
files, minified files (`*.min.*`), files marked `linguist-generated` in
`.gitattributes`, files matching a `Generated:` line in the `## Developer notes`
of the project's CLAUDE.md (comma-separated globs or directories), and files
over 100 KB after the change. Each gets a line `skipped: <file> (<size>, <reason>)`
at the top of the diff file and an entry in `skipped`.

    review_diff.py --from <rev|empty> [--to <rev>] --out loc/review/018.diff [--paths a.py b/] [--exclude tests/]

Prints JSON {"from", "to", "out", "files", "skipped", "empty"}. Exit 0, or 2 when git fails.
"""

import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import git, snapshot  # noqa: E402


LOCKS = {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "poetry.lock",
         "Pipfile.lock", "uv.lock", "pdm.lock", "Cargo.lock", "Gemfile.lock", "composer.lock", "go.sum",
         "packages.lock.json", "flake.lock", "mix.lock", "pubspec.lock", "Podfile.lock"}
LARGE = 100 * 1024
BATCH = 100  # files per git diff call


def generated_patterns(project: Path) -> list:
    """Globs from `Generated:` lines under `## Developer notes` of CLAUDE.md."""
    try:
        text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    except OSError:
        return []
    section = re.split(r"^## Developer notes[^\n]*$", text, maxsplit=1, flags=re.M)
    if len(section) < 2:
        return []
    body = re.split(r"^## ", section[1], maxsplit=1, flags=re.M)[0]
    patterns = []
    for line in body.splitlines():
        match = re.match(r"^\s*(?:[-*]\s*)?Generated:\s*(.+)$", line)
        if match:
            patterns += [item.strip().strip("`") for item in match.group(1).split(",") if item.strip().strip("`")]
    return patterns


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/"):
        return path.startswith(pattern) or ("/" + pattern) in ("/" + path)
    name = path.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(path, pattern) or ("/" not in pattern and fnmatch.fnmatch(name, pattern))


def size_text(size: int) -> str:
    return f"{size} B" if size < 1024 else f"{round(size / 1024)} KB"


def skipped_files(project: Path, end: str, files: list) -> list:
    """The changed files nobody reviews by reading, each {"file", "size", "reason"}."""
    if not files:
        return []
    # Whole trees and stdin, never the file list on the command line: a whole-project
    # review lists thousands of files, over the Windows command-line limit.
    wanted = set(files)
    sizes = {}
    for line in git(["-c", "core.quotePath=false", "ls-tree", "-r", "-l", end], project).splitlines():
        meta, _, name = line.partition("\t")
        parts = meta.split()
        if name in wanted and len(parts) == 4 and parts[3].isdigit():
            sizes[name] = int(parts[3])
    generated = set()
    # NUL-separated (-z): on Windows a text-mode stdin turns "\n" into "\r\n", part of the path.
    fields = git(["check-attr", "-z", "--stdin", "linguist-generated"], project,
                 stdin="".join(f"{path}\0" for path in files), strip=False).split("\0")
    for name, _attr, value in zip(fields[0::3], fields[1::3], fields[2::3]):
        if value in ("set", "true"):
            generated.add(name)
    patterns = generated_patterns(project)
    result = []
    for path in files:
        name = path.rsplit("/", 1)[-1]
        size = sizes.get(path, 0)  # 0: deleted
        if name in LOCKS:
            reason = "lock file"
        elif ".min." in name:
            reason = "minified"
        elif path in generated:
            reason = "linguist-generated"
        elif any(matches(path, pattern) for pattern in patterns):
            reason = "Generated: in CLAUDE.md"
        elif size > LARGE:
            reason = "over 100 KB"
        else:
            continue
        result.append({"file": path, "size": size_text(size), "reason": reason})
    return result


def head_exists(project: Path) -> bool:
    try:
        return bool(git(["rev-parse", "--verify", "-q", "HEAD"], project))
    except RuntimeError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--from", dest="start", required=True, help="start revision or snapshot; empty: the empty tree")
    parser.add_argument("--to", dest="end", help="end revision (default: a fresh snapshot)")
    parser.add_argument("--out", type=Path, required=True, help="diff file to write")
    parser.add_argument("--paths", nargs="*", help="limit the diff to these paths")
    parser.add_argument("--exclude", nargs="*", default=[], help="leave these paths out")
    args = parser.parse_args()
    if args.paths == []:
        # `--paths` with nothing after it would review the whole project.
        parser.error("--paths needs at least one path")

    project = args.project.resolve()
    out = args.out if args.out.is_absolute() else project / args.out
    try:
        end = args.end or snapshot(project)
        if args.start == "empty" or (args.start == "HEAD" and not head_exists(project)):
            # No commits yet: everything in the project is the change.
            args.start = git(["hash-object", "-t", "tree", "--stdin"], project, stdin="")
        scope = ["--", *(args.paths or ["."]), ":!loc", *(f":!{path}" for path in args.exclude)]
        files = git(["-c", "core.quotePath=false", "diff", "--name-only", args.start, end, *scope],
                    project).splitlines()
        skipped = skipped_files(project, end, files)
        left_out = {item["file"] for item in skipped}
        files = [path for path in files if path not in left_out]
        # The kept files in batches, so no command line grows with the project.
        diff = "".join(git(["diff", args.start, end, "--", *(f":(literal){path}" for path in files[i:i + BATCH])],
                           project, strip=False) for i in range(0, len(files), BATCH))
        header = "".join(f"skipped: {item['file']} ({item['size']}, {item['reason']})\n" for item in skipped)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((header + diff).encode("utf-8"))
    except (RuntimeError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    print(json.dumps({"from": args.start, "to": end, "out": out.relative_to(project).as_posix()
                      if out.is_relative_to(project) else out.as_posix(),
                      "files": files, "skipped": skipped, "empty": not files}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
