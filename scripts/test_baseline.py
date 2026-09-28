#!/usr/bin/env python3
"""Copy a project's tests at the start of a plan, and compare them later.

The test files are found from section (e) of `loc/TEST-PLAN.md`: every inline
code token there (outside HTML comments) that is an existing directory, an
existing file or a glob such as `test_*.py`. The copy goes, with
`loc/TEST-PLAN.md` itself, to `loc/state/<NNN>/baseline/`, and
`manifest.json` there lists each file's sha256. Works without git: tests may be
ignored by it.

    test_baseline.py --plan 018             -> copy (an existing copy is kept)
    test_baseline.py --plan 018 --compare   -> {"added", "changed", "removed"}

A project without `loc/TEST-PLAN.md` has nothing to copy yet (the first plan
with code creates it): a message and exit 0. Exit 1 when `--compare` finds no
copy, 2 on a read or write error.
"""

import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

TEST_PLAN = "loc/TEST-PLAN.md"
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
TOKEN = re.compile(r"`([^`\s]+)`")
SKIP = {"__pycache__", ".git", "node_modules"}


def section_e(text: str) -> str:
    match = re.search(r"^## \(e\)[^\n]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return COMMENT.sub("", match.group(1)) if match else ""


def test_files(project: Path) -> list:
    """Relative POSIX paths of the test files named in TEST-PLAN (e), plus TEST-PLAN itself."""
    found = {TEST_PLAN}
    for token in TOKEN.findall(section_e((project / TEST_PLAN).read_text(encoding="utf-8"))):
        token = token.rstrip("/")
        if ".." in Path(token).parts or Path(token).is_absolute():
            continue
        if any(c in token for c in "*?["):
            candidates = project.glob(token)
        elif (project / token).is_dir():
            candidates = (project / token).rglob("*")
        else:
            candidates = [project / token]
        for path in candidates:
            rel = path.relative_to(project)
            if path.is_file() and not SKIP & set(rel.parts) and rel.parts[0] != "loc":
                found.add(rel.as_posix())
    return sorted(found)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create(project: Path, baseline: Path) -> dict:
    manifest = baseline / "manifest.json"
    if manifest.is_file():
        return {"baseline": baseline.relative_to(project).as_posix(), "created": False,
                "message": "copy already exists, kept (resumed plan)"}
    files = {}
    for rel in test_files(project):
        target = baseline / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / rel, target)
        files[rel] = sha256(project / rel)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    manifest.write_text(json.dumps({"created": now, "files": files}, indent=2) + "\n", encoding="utf-8")
    return {"baseline": baseline.relative_to(project).as_posix(), "created": True, "files": sorted(files)}


def compare(project: Path, baseline: Path) -> dict:
    old = json.loads((baseline / "manifest.json").read_text(encoding="utf-8"))["files"]
    now = {rel: sha256(project / rel) for rel in test_files(project)}
    now.update({rel: sha256(project / rel) for rel in old if (project / rel).is_file()})
    return {
        "baseline": baseline.relative_to(project).as_posix(),
        "added": sorted(set(now) - set(old)),
        "changed": sorted(rel for rel in set(now) & set(old) if now[rel] != old[rel]),
        "removed": sorted(set(old) - set(now)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path("."), help="project root (default: .)")
    parser.add_argument("--plan", required=True, help="plan number, e.g. 018")
    parser.add_argument("--compare", action="store_true", help="compare the tests with the copy")
    args = parser.parse_args()
    project = args.project.resolve()
    baseline = project / "loc" / "state" / args.plan / "baseline"

    if not (project / TEST_PLAN).is_file():
        print(json.dumps({"message": f"no {TEST_PLAN} yet: nothing to copy"}))
        return 0
    try:
        if args.compare:
            if not (baseline / "manifest.json").is_file():
                print(json.dumps({"error": f"no copy in {baseline.relative_to(project).as_posix()}"}))
                return 1
            result = compare(project, baseline)
        else:
            result = create(project, baseline)
    except (OSError, UnicodeDecodeError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
