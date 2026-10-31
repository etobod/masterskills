#!/usr/bin/env python3
"""Set up the masterskills structure in a project, adding only what is missing.

Creates `loc/inbox/`, `loc/inbox/done/`, `loc/PRD.md`, `loc/PATTERNS.md`,
`loc/MEMORY.md`, the standard `CLAUDE.md` sections, a `loc/` entry in
`.gitignore` and `.claude/settings.json` (no auto memory, no AI
attribution). Existing files are never overwritten: a missing `CLAUDE.md` section,
`.gitignore` entry or settings value is added, everything else is left alone,
so running it again is safe. A project without git is refused and nothing is
created.

On Windows it also leaves a launcher for the tool that runs it, unless one
exists: `claude.bat` resumes the Claude Code session given by `--session`;
`open-code.bat` (plugin built for OpenCode, which records its source
repository in `SOURCE`) updates the plugin from that repository and starts
OpenCode.

`empty` lists the sections that hold nothing but the template's comment or
`<placeholder>`: the ones `loc-init` may fill from a brainstorm.

`--check` writes nothing. After filling sections from a brainstorm it prints
{"ok": true, "project": ..., "empty": {...}, "not_english": [...]}, where
`not_english` lists the `CLAUDE.md` sections holding Polish letters
(`CLAUDE.md` is written in English).

Prints JSON to stdout:
    {"ok": true, "project": ..., "created": [...], "updated": [{"path", "added"}],
     "existing": [...], "skipped": [{"path", "reason"}],
     "empty": {"CLAUDE.md": [...], "loc/PRD.md": [...]}}
or, without git (exit code 2):
    {"ok": false, "project": ..., "error": "no-git", "message": ...}
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from migrate import FORMAT

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"

DIRS = ["loc/inbox", "loc/inbox/done", "loc/diagrams", "loc/diagrams/tmp"]
DOCS = ["loc/PRD.md", "loc/PATTERNS.md", "loc/MEMORY.md"]
LOC_ENTRY = re.compile(r"^/?loc(/(\*\*?)?)?\s*$")
PRD_FRAME = ["Goal", "Core idea", "Scenarios"]  # Directions is work to plan, not the project's frame
POLISH = re.compile("[\u0104\u0105\u0106\u0107\u0118\u0119\u0141\u0142\u0143\u0144\u00d3\u00f3\u015a\u015b\u0179\u017a\u017b\u017c]")
PLACEHOLDER = re.compile(r"<!--.*?-->|^#*\s*<[^>\n]*>\s*$", re.S | re.M)

SESSION = re.compile(r"^[\w-]+$")
CLAUDE_BAT = """@rem Resumes the Claude Code session in which loc-init ran.
@cd /d "%~dp0"
@set "CLAUDE=claude.exe"
@where claude.exe >nul 2>nul || set "CLAUDE=%USERPROFILE%\\.local\\bin\\claude.exe"
@"%CLAUDE%" --resume {session} %*
@exit /b %ERRORLEVEL%
"""
# Launchers before 2.12.2 ran `claude`, which in the project directory is claude.bat itself.
OLD_CLAUDE_BAT = re.compile(r'\A@rem Resumes the Claude Code session in which loc-init ran\.\r?\n'
                            r'@cd /d "%~dp0"\r?\n@set "CLAUDE=claude"\r?\n'
                            r'@where claude >nul 2>nul \|\| set "CLAUDE=%USERPROFILE%\\\.local\\bin\\claude\.exe"\r?\n'
                            r'@"%CLAUDE%" --resume ([\w-]+) %\*\r?\n@exit /b %ERRORLEVEL%\r?\n\Z')
OPENCODE_BAT = """@rem Updates masterskills for OpenCode, then starts OpenCode in this project.
@cd /d "%~dp0"
@call "{installer}"
@cd /d "%~dp0"
@opencode %*
@exit /b %ERRORLEVEL%
"""

NO_GIT = (
    "This directory is not the root of a git repository. masterskills needs git: plans take a "
    "snapshot of every milestone with git, reviews read the diff "
    "and commits close the work. Nothing was created; with `git init` it can "
    "go on."
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


def ensure_launcher(project: Path, report: dict, session: str) -> None:
    if sys.platform != "win32":
        return
    source = PLUGIN_ROOT / "SOURCE"
    if (PLUGIN_ROOT / ".claude-plugin").is_dir():
        name = "claude.bat"
        text = CLAUDE_BAT.format(session=session) if SESSION.match(session) else None
    elif source.is_file():
        name = "open-code.bat"
        installer = Path(source.read_text(encoding="utf-8").strip()) / "opencode-install.bat"
        text = OPENCODE_BAT.format(installer=installer)
    else:
        return
    old = OLD_CLAUDE_BAT.match((project / name).read_text(encoding="utf-8", errors="replace")) \
        if name == "claude.bat" and (project / name).is_file() else None
    if old:
        write(project / name, CLAUDE_BAT.format(session=old.group(1)).replace("\n", "\r\n"))
        report["updated"].append({"path": name, "added": ["runs claude.exe, not claude.bat itself"]})
    elif (project / name).exists():
        report["existing"].append(name)
    elif text is None:
        report["skipped"].append({"path": name, "reason": "no session id to resume: run it from the loc-init skill"})
    else:
        write(project / name, text.replace("\n", "\r\n"))
        report["created"].append(name)


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


def section_bodies(path: Path) -> dict:
    """Each `## ` section's body, template comments and placeholders removed."""
    if not path.is_file():
        return {}
    text = path.read_bytes().decode("utf-8", errors="replace")
    parts = re.split(r"(?m)^(?=## )", text)
    return {p.splitlines()[0][3:].strip(): PLACEHOLDER.sub("", p.partition("\n")[2]).strip()
            for p in parts if p.startswith("## ")}


def empty_sections(path: Path, names: list, missing_is_empty: bool = False) -> list:
    """The sections among `names` whose body is only template comments or placeholders.
    With `missing_is_empty`, a section without its heading counts too."""
    if not path.is_file():
        return []
    bodies = section_bodies(path)
    return [name for name in names if not bodies.get(name) and (name in bodies or missing_is_empty)]


def empty_report(project: Path) -> dict:
    return {
        "CLAUDE.md": empty_sections(project / "CLAUDE.md", [name for name, _ in claude_sections()]),
        # A PRD older than one of its frame sections lacks the heading: it is still to be filled.
        "loc/PRD.md": empty_sections(project / "loc" / "PRD.md", PRD_FRAME, missing_is_empty=True),
    }


def check(project: Path) -> dict:
    bodies = section_bodies(project / "CLAUDE.md")
    names = [name for name, _ in claude_sections()]
    return {"ok": True, "project": project.as_posix(), "empty": empty_report(project),
            "not_english": [name for name in names if POLISH.search(bodies.get(name, ""))]}


def init(project: Path, session: str = "") -> dict:
    report = {"ok": True, "project": project.as_posix(), "created": [], "updated": [], "existing": [],
              "skipped": []}

    fresh = not (project / "loc").exists()
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
            write(path, text.replace("{PROJECT}", project.name))
            report["created"].append(rel)

    if fresh:
        write(project / "loc" / "VERSION", f"{FORMAT}\n")
        report["created"].append("loc/VERSION")

    ensure_claude_md(project, report)
    ensure_gitignore(project, report)
    ensure_settings(project, report)
    ensure_launcher(project, report, session)
    report["empty"] = empty_report(project)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)",
    )
    parser.add_argument("--check", action="store_true",
                        help="write nothing; report empty sections and CLAUDE.md sections not in English")
    parser.add_argument("--session", default="", help="Claude Code session id for claude.bat to resume")
    args = parser.parse_args()
    project = args.project.resolve()

    if not project.is_dir():
        print(json.dumps({"ok": False, "project": project.as_posix(), "error": "not-a-directory",
                          "message": f"{project} is not a directory. Nothing was created."}))
        return 2
    if not has_git(project):
        print(json.dumps({"ok": False, "project": project.as_posix(), "error": "no-git", "message": NO_GIT}))
        return 2

    print(json.dumps(check(project) if args.check else init(project, args.session), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
