#!/usr/bin/env python3
"""Find tests that define their own copy of a function from the project's code.

A test that copies `fft` from `fourier.html` instead of running it passes
whatever the page does. Run in the project directory:

    test_copies.py

Prints JSON `{"copies": [{"name", "test", "test_line", "source", "source_line",
"similarity"}]}`: each function a test file defines under the same name as a
code file, with a body of at least MIN_LINES lines that is at least SIMILAR
alike. Python `def`, JavaScript `function` and `const name = (...) =>`, also
inside a page's `<script>`. A test helper that shares only a name is not a
copy. Still a hint, not proof: a mock may look like what it replaces. Works
without git.
"""

import difflib
import json
import os
import re
import sys
from pathlib import Path

SKIP = {"__pycache__", ".git", "node_modules", "loc", ".venv", "venv", "dist", "build"}
SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".htm"}
COMMON = {"main", "setup", "teardown", "setUp", "tearDown", "setUpClass", "tearDownClass", "__init__"}
DEFINITION = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:"
    r"def\s+(?P<py>\w+)\s*\("
    r"|function\s*\*?\s*(?P<fn>\w+)\s*\("
    r"|(?:const|let|var)\s+(?P<var>\w+)\s*=\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|\w+\s*=>)"
    r")")
MIN_LINES = 3
SIMILAR = 0.6
TEST_NAME = re.compile(r"(^test_.*|.*_test\.\w+$|.*\.(test|spec)\.\w+$)")
TEST_DIRS = {"test", "tests", "spec", "__tests__"}


def files(project: Path):
    found = []
    for root, dirs, names in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP]  # never walk into node_modules, .venv, ...
        for name in names:
            if Path(name).suffix in SUFFIXES and (Path(root) / name).is_file():  # no broken links
                found.append((Path(root) / name).relative_to(project))
    yield from sorted(found)


def is_test(rel: Path) -> bool:
    return bool(TEST_NAME.match(rel.name)) or bool(TEST_DIRS.intersection(rel.parts[:-1]))


def body(lines: list, start: int) -> list:
    """The function starting at lines[start]: by braces, else by indentation."""
    first = lines[start]
    if "{" in first or (start + 1 < len(lines) and lines[start + 1].strip().startswith("{")):
        depth, out = 0, []
        for line in lines[start:start + 400]:
            out.append(line)
            depth += line.count("{") - line.count("}")
            if depth <= 0 and "{" in "".join(out):
                break
    else:
        indent = len(first) - len(first.lstrip())
        out = [first]
        for line in lines[start + 1:start + 400]:
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            out.append(line)
    code = [re.sub(r"\s+", " ", l.split("//")[0].split("#")[0]).strip() for l in out[1:]]
    return [l for l in code if l and l not in "{}"]


def definitions(path: Path) -> dict:
    """name -> (first line number, body lines)."""
    found = {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        match = DEFINITION.match(line)
        if match:
            name = match.group("py") or match.group("fn") or match.group("var")
            if name not in COMMON and not name.startswith("test") and name not in found:
                found[name] = (index + 1, body(lines, index))
    return found


def main() -> int:
    project = Path.cwd()
    tests, sources = [], {}
    for rel in files(project):
        if is_test(rel):
            tests.append(rel)
        else:
            for name, (number, code) in definitions(project / rel).items():
                sources.setdefault(name, []).append((rel.as_posix(), number, code))
    copies = []
    for rel in tests:
        for name, (number, code) in definitions(project / rel).items():
            if name not in sources or len(code) < MIN_LINES:
                continue
            similarity, source, source_line = max(
                (difflib.SequenceMatcher(None, code, original, autojunk=False).ratio(), source, source_line)
                for source, source_line, original in sources[name])
            if similarity >= SIMILAR:
                copies.append({"name": name, "test": rel.as_posix(), "test_line": number,
                               "source": source, "source_line": source_line,
                               "similarity": round(similarity, 2)})
    print(json.dumps({"copies": copies}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
