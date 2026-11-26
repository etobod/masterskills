#!/usr/bin/env python3
"""Measure the test suite against the code and say when a whole-suite review is due.

Counts the lines of the project's test files and of its code (tracked and new
files, `loc/` left out). Test files are the given `--tests` paths, else those
found at any depth (`tests/`, `test/`, `*.test.*`, `*.spec.*`, `*_test.*`,
`test_*`). Code is every other file with a source extension, minified files and
files over 100 KB left out.

    suite_size.py [--tests tests/ web/test_a.py] [--record <plan>] [--reviewed]

`--record` appends `<date> <plan> suite-size tests=<n> code=<n>` to
`loc/state/qa-history.log`; `--reviewed` appends a `suite-review` line, written
when the whole suite was reviewed. A review is due when the tests grew by half
since the last `suite-review` line or, with none, when they are over twice the code.

Prints JSON {"tests", "code", "reviewed_at", "due", "reason"}. Exit 0, or 2 when git fails.
"""

import argparse
import datetime
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import git  # noqa: E402

CODE = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".htm", ".css", ".scss", ".vue", ".svelte",
        ".go", ".rs", ".java", ".kt", ".cs", ".rb", ".php", ".c", ".h", ".cpp", ".hpp", ".swift", ".sh", ".ps1",
        ".lua", ".dart", ".scala", ".sql"}
LARGE = 100 * 1024
HISTORY = Path("loc/state/qa-history.log")
GROWTH = 1.5   # tests grown by half since the last review
RATIO = 2.0    # tests over twice the code, with no review yet


def matches(path: str, given: str) -> bool:
    """A given test path: a file, a directory or a glob."""
    return path == given or path.startswith(given + "/") or fnmatch.fnmatch(path, given)


def is_test(path: str, given: list) -> bool:
    if given:
        return any(matches(path, g) for g in given)
    parts = path.split("/")
    name = parts[-1]
    return (any(part in ("tests", "test") for part in parts[:-1])
            or any(fnmatch.fnmatch(name, p) for p in ("*.test.*", "*.spec.*", "*_test.*", "test_*")))


def lines(path: Path) -> int:
    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def measure(project: Path, given: list) -> tuple:
    names = git(["-c", "core.quotePath=false", "ls-files", "-co", "--exclude-standard"], project).splitlines()
    missing = [g for g in given if not any(matches(name, g) for name in names)]
    if missing:
        # A path that matches nothing would count no tests and never say a review is due.
        raise RuntimeError(f"no file matches the test path {missing[0]}")
    tests = code = 0
    for name in names:
        if name == "loc" or name.startswith("loc/"):
            continue
        path = project / name
        # Source files only, on both sides: fixtures and recorded data are not tests.
        if Path(name).suffix.lower() not in CODE or ".min." in name:
            continue
        try:
            if path.stat().st_size > LARGE:
                continue
        except OSError:
            continue
        if is_test(name, given):
            tests += lines(path)
        else:
            code += lines(path)
    return tests, code


def last_review(history: Path):
    try:
        text = history.read_text(encoding="utf-8")
    except OSError:
        return None
    found = None
    for line in text.splitlines():
        match = re.match(r"^(\S+) \S+ suite-review tests=(\d+) code=(\d+)", line)
        if match:
            found = (match.group(1), int(match.group(2)))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--tests", nargs="*", default=[], help="test paths (default: found at any depth)")
    parser.add_argument("--record", metavar="PLAN", help="append a suite-size line for this plan")
    parser.add_argument("--reviewed", action="store_true", help="append a suite-review line")
    args = parser.parse_args()
    project = args.project.resolve()
    try:
        given = [t.replace("\\", "/").removeprefix("./").rstrip("/") for t in args.tests]
        tests, code = measure(project, given)
    except RuntimeError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    history = project / HISTORY
    review = last_review(history)
    if review:
        due = tests >= GROWTH * review[1] and tests > review[1]
        reason = f"tests {tests} lines, {review[1]} at the review of {review[0]}"
    else:
        due = tests > RATIO * code
        reason = f"tests {tests} lines, code {code}, no suite review yet"
    today = datetime.date.today().isoformat()
    entries = []
    if args.record:
        entries.append(f"{today} {args.record} suite-size tests={tests} code={code}")
    if args.reviewed:
        entries.append(f"{today} - suite-review tests={tests} code={code}")
        due, reason = False, "reviewed now"
    if entries:
        history.parent.mkdir(parents=True, exist_ok=True)
        with history.open("a", encoding="utf-8") as handle:
            handle.write("".join(entry + "\n" for entry in entries))
    print(json.dumps({"tests": tests, "code": code, "reviewed_at": review[0] if review else None,
                      "due": due, "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
