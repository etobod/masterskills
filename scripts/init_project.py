#!/usr/bin/env python3
"""Set up the masterskills structure in a project, adding only what is missing.

Creates `loc/inbox/`, `loc/inbox/done/`, `loc/PRD.md`, `loc/PATTERNS.md`,
`loc/MEMORY.md`, the standard `CLAUDE.md` sections, a `loc/` entry in
`.gitignore` and `.claude/settings.json` (no auto memory, no AI
attribution). Existing files are never overwritten: a missing `CLAUDE.md` section,
`.gitignore` entry or settings value is added, everything else is left alone,
so running it again is safe. A project without git is refused and nothing is
created.

Prints JSON to stdout:
    {"ok": true, "project": ..., "created": [...], "updated": [{"path", "added"}],
     "existing": [...], "skipped": [{"path", "reason"}]}
or, without git (exit code 2):
    {"ok": false, "project": ..., "error": "no-git", "message": ...}
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"

DIRS = ["loc/inbox", "loc/inbox/done"]
DOCS = ["loc/PRD.md", "loc/PATTERNS.md", "loc/MEMORY.md"]
LOC_ENTRY = re.compile(r"^/?loc(/(\*\*?)?)?\s*$")

NO_GIT = (
    "This directory is not the root of a git repository. masterskills needs git: plans take a "
    "snapshot of every milestone with git, reviews read the diff "
    "and commits close the work. Run `git init` and then this again. Nothing "
    "was created."
)


def has_git(project: Path) -> bool:
    # The project root must be the repository root: a `.git` further up belongs
    # to some other repository, not to this project.
    return (project / ".git").exists()


def newline_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def append(path: Path, text: str, block: str) -> None:
    nl = newline_of(text)
    if text and not text.endswith(("\n", "\r")):
        text += nl
    if text.strip():
        text += nl
    write(path, text + block.replace("\n", nl))


def claude_sections() -> list:
    """Split templates/CLAUDE.md into (heading, block) pairs."""
    text = (TEMPLATES / "CLAUDE.md").read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(?=## )", text)
    return [(p.splitlines()[0][3:].strip(), p.rstrip() + "\n") for p in parts if p.startswith("## ")]


def ensure_claude_md(project: Path, report: dict) -> None:
    path = project / "CLAUDE.md"
    sections = claude_sections()
    if not path.exists():
        body = "\n".join(block for _, block in sections)
        write(path, f"# {project.name}\n\n{body}")
        report["created"].append("CLAUDE.md")
        return

    text = path.read_bytes().decode("utf-8")
    missing = [
        (name, block) for name, block in sections
        if not re.search(rf"(?mi)^#+\s*{re.escape(name)}\s*$", text)
    ]
    if not missing:
        report["existing"].append("CLAUDE.md")
        return
    append(path, text, "\n".join(block for _, block in missing))
    report["updated"].append({"path": "CLAUDE.md", "added": [name for name, _ in missing]})


def ensure_gitignore(project: Path, report: dict) -> None:
    path = project / ".gitignore"
    if not path.exists():
        write(path, "loc/\n")
        report["created"].append(".gitignore")
        return
    text = path.read_bytes().decode("utf-8")
    if any(LOC_ENTRY.match(line.strip()) for line in text.splitlines()):
        report["existing"].append(".gitignore")
        return
    append(path, text, "# masterskills: workflow files, never in git\nloc/\n")
    report["updated"].append({"path": ".gitignore", "added": ["loc/"]})


def merge(settings: dict, template: dict, prefix: str = "") -> list:
    """Add what the template has and settings lack; return the dotted names added.

    Objects are merged key by key and lists gain their missing items; a value
    the user already set is never changed.
    """
    added = []
    for key, value in template.items():
        name = prefix + key
        if key not in settings:
            settings[key] = value
            added.append(name)
        elif isinstance(value, dict) and isinstance(settings[key], dict):
            added += merge(settings[key], value, name + ".")
        elif isinstance(value, list) and isinstance(settings[key], list):
            for item in value:
                if item not in settings[key]:
                    settings[key].append(item)
                    added.append(f"{name}: {item}")
    return added


def ensure_settings(project: Path, report: dict) -> None:
    path = project / ".claude" / "settings.json"
    template = json.loads((TEMPLATES / "settings.json").read_text(encoding="utf-8"))
    if not path.exists():
        write(path, json.dumps(template, indent=2) + "\n")
        report["created"].append(".claude/settings.json")
        return
    try:
        text = path.read_bytes().decode("utf-8-sig")
        settings = json.loads(text)
    except ValueError as error:  # UnicodeDecodeError is a ValueError too
        report["skipped"].append({"path": ".claude/settings.json", "reason": f"not valid UTF-8 JSON: {error}"})
        return
    if not isinstance(settings, dict):
        report["skipped"].append({"path": ".claude/settings.json", "reason": "not a JSON object"})
        return
    missing = merge(settings, template)
    if not missing:
        report["existing"].append(".claude/settings.json")
        return
    nl = newline_of(text)
    write(path, (json.dumps(settings, indent=2, ensure_ascii=False) + "\n").replace("\n", nl))
    report["updated"].append({"path": ".claude/settings.json", "added": missing})


def init(project: Path) -> dict:
    report = {"ok": True, "project": project.as_posix(), "created": [], "updated": [], "existing": [],
              "skipped": []}

    for rel in DIRS:
        path = project / rel
        if path.is_dir():
            report["existing"].append(rel + "/")
        else:
            path.mkdir(parents=True)
            report["created"].append(rel + "/")

    for rel in DOCS:
        path = project / rel
        if path.exists():
            report["existing"].append(rel)
        else:
            text = (TEMPLATES / "loc" / path.name).read_text(encoding="utf-8")
            write(path, text.replace("{PROJEKT}", project.name))
            report["created"].append(rel)

    ensure_claude_md(project, report)
    ensure_gitignore(project, report)
    ensure_settings(project, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)",
    )
    project = parser.parse_args().project.resolve()

    if not project.is_dir():
        print(json.dumps({"ok": False, "project": project.as_posix(), "error": "not-a-directory",
                          "message": f"{project} is not a directory. Nothing was created."}))
        return 2
    if not has_git(project):
        print(json.dumps({"ok": False, "project": project.as_posix(), "error": "no-git", "message": NO_GIT}))
        return 2

    print(json.dumps(init(project), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
