#!/usr/bin/env python3
"""Write the diff under review to a file and list the changed files.

`loc/` is left out: plans, reviews and questions are not the code under
review. Without `--to` the end point is a fresh snapshot of the working tree
(new files included, see snapshot.py), so uncommitted work is reviewed too.
`--from HEAD` in a repository with no commits starts from the empty tree.

Files nobody reviews by reading are left out of the diff and of `files`: lock
files, minified files (`*.min.*`), files marked `linguist-generated` in
`.gitattributes`, files matching a `Generated:` line in the `## Developer notes`
of the project's CLAUDE.md (comma-separated globs or directories), and files
over 100 KB after the change. Each gets a line `skipped: <file> (<size>, <reason>)`
at the top of the diff file and an entry in `skipped`.

    review_diff.py --from <rev> [--to <rev>] --out loc/review/018.diff [--paths a.py b/]

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
    sizes = {}
    for line in git(["ls-tree", "-r", "-l", end, "--", *files], project).splitlines():
        meta, _, name = line.partition("\t")
        parts = meta.split()
        if len(parts) == 4 and parts[3].isdigit():
            sizes[name] = int(parts[3])
    generated = set()
    for line in git(["check-attr", "linguist-generated", "--", *files], project).splitlines():
        name, _, value = line.rpartition(": ")
        if value in ("set", "true"):
            generated.add(name.rsplit(": linguist-generated", 1)[0])
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
        files = git(["diff", "--name-only", args.start, end, *scope], project).splitlines()
        skipped = skipped_files(project, end, files)
        left_out = {item["file"] for item in skipped}
        files = [path for path in files if path not in left_out]
        scope += [f":(exclude,literal){path}" for path in sorted(left_out)]
        diff = git(["diff", args.start, end, *scope], project, strip=False)
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
