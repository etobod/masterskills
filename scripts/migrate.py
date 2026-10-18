#!/usr/bin/env python3
"""Bring a project's `loc/` up to the plugin's current format, one step at a time.

`loc/VERSION` holds the format number; a `loc/` without it is format 1. Each
step is deterministic and writes `loc/VERSION`, so a second run changes nothing.

Step 1 -> 2 (Polish structure -> English structure):
  - inbox files of the old types are renamed (`NNN-pytanie-x.md` -> `NNN-question-x.md`)
    in `loc/inbox/` and `loc/inbox/done/`, and every reference to them in `loc/` follows;
  - headings, `**Field:**` names, status and type values, criterion and review-note
    markers are replaced where they start a line; prose is never touched;
  - `CLAUDE.md` gets `## User language` = Polish (format 1 was always Polish);
  - `translate` lists the live documents whose prose the model translates:
    `PRD.md`, `PATTERNS.md`, `TEST-PLAN.md`, the head of `MEMORY.md` and the open
    inbox files except questions. `done/` and old journal entries stay as history.

Step 2 -> 3 (recorded decisions):
  - `loc/PRD.md` gets an empty `## Decisions` section before `## Directions`;
  - `harvest` is true when that section holds no decision while `loc/inbox/done/`
    holds plans: the model then asks the `architect` agent to propose them.

Step 3 -> 4 (plan priorities):
  - `loc/PRD.md` gets an empty `## Priorities` section, written only by the user;
  - an open plan without a group in its name, not running, that fails
    `check_plan.py --ready` on its own content becomes a deferred item:
    `NNN-plan-x.md` -> `NNN-deferred-x.md`, `**Type:** deferred` and a
    `**Deferred:**` line with the first problem; the rest of the text is kept.

`regroup` is true while an open plan, not running, has no group: the model asks
the `pm` agent to order the queue.

Prints JSON: {"project", "from", "to", "renamed": [[old, new], ...], "changed": [...], "translate": [...],
"harvest": bool, "deferred": [[old, new], ...], "regroup": bool}
`from` is null when the project has no `loc/`.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

FORMAT = 4

TYPES = {"pytanie": "question", "odlozone": "deferred", "przeglad": "review", "utknelo": "stuck"}
OLD_NAME = re.compile(r"^(\d{3,})-(" + "|".join(TYPES) + r")-(.+)$")
RENAMED_STATE = {"qa-historia.log": "qa-history.log", "mutacja.json": "mutation.json", "mutacja": "mutation"}

HEADINGS = {
    "Cel": "Goal", "Czego nie robimy": "Out of scope", "Nie bronimy przed": "Not defended against",
    "Kontekst z kodu": "Code context", "Kamienie milowe": "Milestones", "Ryzyka i decyzje": "Risks and decisions",
    "Bramka planu": "Plan gate", "Uwagi z przeglądów": "Review notes", "Fragment PRD": "PRD fragment",
    "Rozstrzygnięcie": "Resolution", "Wynik": "Result",
    "Temat": "Topic", "Notatki": "Notes", "Decyzje": "Decisions", "Otwarte": "Open",
    "Co odłożono": "What was deferred", "Dlaczego nie teraz": "Why not now", "Kiedy wrócić": "When to return",
    "Zakres": "Scope", "Uwagi": "Findings",
    "Pytanie": "Question", "Kontekst": "Context", "Warianty": "Options", "Tymczasowo": "Interim",
    "Gdzie wystąpiło": "Where it came up",
    "Rundy": "Rounds", "Co zostało": "What remains", "Co zrobiono dalej": "What happened next",
    "bramka planu": "plan gate",
    "Rdzeń idei": "Core idea", "Scenariusze": "Scenarios", "Kierunki": "Directions",
    "Wzorce": "Patterns", "✅ Działa": "✅ Works", "❌ Nie działa": "❌ Does not work", "⚠️ Pułapki": "⚠️ Pitfalls",
    "Dziennik": "Journal", "Plan testów": "Test plan",
    "(a) Warstwy i komendy": "(a) Layers and commands",
    "(b) Co się zmieniło → co rozszerzyć": "(b) What changed → what to extend",
    "(c) Stałe macierze": "(c) Fixed matrices", "(d) Granice": "(d) Limits",
    "(e) Jak tu wygląda test": "(e) What a test looks like here",
}
FIELDS = {
    "Typ": "Type", "Utworzono": "Created", "Źródło": "Source", "Kategoria": "Category",
    "Kryteria": "Criteria", "Bez testów": "No tests", "Wykonawca": "Performer", "Dowód": "Proof",
    "Sprawdzenie ręczne": "Manual check", "Kiedy stosować": "When to use", "Werdykt": "Verdict",
    "Data": "Date", "Zakres": "Scope",
}
VALUES = {
    "Type": dict(TYPES),
    "Status": {"otwarte — QA nie przeszło": "open — QA failed", "otwarte — bramka nie przeszła": "open — gate failed",
               "otwarte": "open", "wykonane": "done", "zamknięte": "closed"},
    "Category": {"nieblokująca": "non-blocking", "blokująca": "blocking"},
    "Performer": {"użytkownik (blokujący)": "user (blocking)", "użytkownik (odkładalny)": "user (deferrable)",
                  "użytkownik": "user"},
    "Source": {"rozmowa": "conversation"},
}
JOURNAL = {"Planowanie": "Planning", "Przegląd": "Review", "Poprawka": "Fix", "Decyzja": "Decision"}
NOTES = {"sugestia": "suggestion", "nierealna": "unrealistic", "dość": "enough"}

HEADING = re.compile(r"^(#{1,6} )(.+?)(\s*)$")
ROUND = re.compile(r"^(#{1,6} )Runda (\d+)(\s*)$")
SUITE = re.compile(r"^(### M1 — )zestaw testów(\s*)$")
FIELD = re.compile(r"^\*\*(" + "|".join(map(re.escape, FIELDS)) + r"|Status):\*\*( ?)(.*)$")
BEHAVIOUR = re.compile(r"^(- K\d+) \(zachowanie\):")
MANUAL = re.compile(r"→ ręcznie(\s*)$")
NONE = re.compile(r"^- brak(\s*)$")
NOTE = re.compile(r"^- (" + "|".join(NOTES) + r") \((M\d+ code-review|final-review|planowanie)\):")
OPTION = re.compile(r"^(- \*\*[A-Z]) \(rekomendowany\)\*\*")
EMPTY = re.compile(r"^<puste do czasu[^>]*>(\s*)$")
JOURNAL_ENTRY = re.compile(r"^(## \d{4}-\d{2}-\d{2} \d{2}:\d{2} — \[)(" + "|".join(JOURNAL) + r")\]")
INDEX_HEADER = re.compile(r"^\| Data \| Typ \| Temat \| Linia \|(\s*)$")
INDEX_ROW = re.compile(r"^(\| \d{4}-\d{2}-\d{2} \d{2}:\d{2} \| )(" + "|".join(JOURNAL) + r")( \|)")
TEXT = {".md", ".json", ".log", ".txt"}


def read_format(loc: Path):
    if not loc.is_dir():
        return None
    try:
        return int((loc / "VERSION").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 1


def value(field: str, rest: str) -> str:
    for old, new in VALUES.get(field, {}).items():
        if rest == old or rest.startswith(old + " "):
            return new + rest[len(old):]
    return rest


def convert_line(line: str) -> str:
    match = ROUND.match(line)
    if match:
        return f"{match.group(1)}Round {match.group(2)}{match.group(3)}"
    match = SUITE.match(line)
    if match:
        return f"{match.group(1)}test suite{match.group(2)}"
    match = JOURNAL_ENTRY.match(line)
    if match:
        return match.group(1) + JOURNAL[match.group(2)] + "]" + line[match.end():]
    match = HEADING.match(line)
    if match and match.group(2) in HEADINGS:
        return match.group(1) + HEADINGS[match.group(2)] + match.group(3)
    match = FIELD.match(line)
    if match:
        field = FIELDS.get(match.group(1), match.group(1))
        return f"**{field}:**{match.group(2)}{value(field, match.group(3))}"
    match = INDEX_HEADER.match(line)
    if match:
        return "| Date | Type | Topic | Line |" + match.group(1)
    match = INDEX_ROW.match(line)
    if match:
        return match.group(1) + JOURNAL[match.group(2)] + line[match.end(2):]
    match = NOTE.match(line)
    if match:
        gate = "planning" if match.group(2) == "planowanie" else match.group(2)
        line = f"- {NOTES[match.group(1)]} ({gate}):" + line[match.end():]
        return line.replace("Kto to wytwarza:", "Who produces it:").replace("Powód:", "Reason:")
    if NONE.match(line):
        return NONE.sub(r"- none\1", line)
    if EMPTY.match(line):
        return EMPTY.sub(r"<empty until handled>\1", line)
    line = BEHAVIOUR.sub(r"\1 (behaviour):", line)
    line = OPTION.sub(r"\1 (recommended)**", line)
    line = MANUAL.sub(r"→ manual\1", line)
    if line.startswith("Przeniesione z loc/PRD.md"):
        line = "Moved from loc/PRD.md" + line[len("Przeniesione z loc/PRD.md"):]
    return line.replace("→ przekazane do ", "→ moved to ")


def convert(text: str, names: dict, markers: bool) -> str:
    for old, new in names.items():
        text = text.replace(old, new)
    if not markers:
        return text
    return "".join(convert_line(line.rstrip("\r\n")) + line[len(line.rstrip("\r\n")):]
                   for line in text.splitlines(keepends=True))


def rename(loc: Path, report: dict) -> dict:
    names = {}
    for folder in (loc / "inbox", loc / "inbox" / "done"):
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            match = OLD_NAME.match(path.name)
            if match:
                new = f"{match.group(1)}-{TYPES[match.group(2)]}-{match.group(3)}"
                path.rename(path.with_name(new))
                names[path.name] = new
                report["renamed"].append([path.relative_to(loc.parent).as_posix(),
                                          path.with_name(new).relative_to(loc.parent).as_posix()])
    for old, new in RENAMED_STATE.items():
        path = loc / "state" / old
        if path.exists() and not (loc / "state" / new).exists():
            path.rename(path.with_name(new))
            names[old] = new
            report["renamed"].append([f"loc/state/{old}", f"loc/state/{new}"])
    return names


def add_user_language(project: Path, report: dict) -> None:
    path = project / "CLAUDE.md"
    if not path.is_file():
        return
    text = path.read_bytes().decode("utf-8")
    if re.search(r"(?m)^## User language\s*$", text):
        return
    nl = "\r\n" if "\r\n" in text else "\n"
    block = f"## User language{nl}Polish{nl}{nl}"
    match = re.search(r"(?m)^## Project-specific workflow\s*$", text)
    if match:
        text = text[:match.start()] + block + text[match.start():]
    else:
        text = text.rstrip("\r\n") + nl + nl + block.rstrip("\r\n") + nl
    path.write_bytes(text.encode("utf-8"))
    report["changed"].append("CLAUDE.md")


def is_question(path: Path) -> bool:
    return "-question-" in path.name


def step_1_to_2(project: Path, report: dict) -> None:
    loc = project / "loc"
    names = rename(loc, report)
    for path in sorted(loc.rglob("*")):
        rel = path.relative_to(loc)
        if not path.is_file() or path.suffix not in TEXT or rel.parts[0] in ("tmp", "review"):
            continue
        text = path.read_bytes().decode("utf-8", errors="surrogateescape")
        new = convert(text, names, markers=path.suffix == ".md")
        if new != text:
            path.write_bytes(new.encode("utf-8", errors="surrogateescape"))
            report["changed"].append(path.relative_to(project).as_posix())
    add_user_language(project, report)
    live = [f"loc/{name}" for name in ("PRD.md", "PATTERNS.md", "TEST-PLAN.md", "MEMORY.md")
            if (loc / name).is_file()]
    live += [f"loc/inbox/{p.name}" for p in sorted((loc / "inbox").glob("*.md")) if not is_question(p)] \
        if (loc / "inbox").is_dir() else []
    report["translate"] = live


DECISIONS = [
    "## Decisions",
    "<!-- Lasting decisions plans follow instead of restating them, one line each:",
    "- D-01: <decision>. Reason: <why>. (<date>)",
    "A replaced decision is removed; the one that replaces it says `replaces D-01: <why>`. -->",
]


def add_section(project: Path, report: dict, lines: list) -> str:
    """Put a section before `## Directions` of `loc/PRD.md` unless it is there; return the PRD text."""
    path = project / "loc" / "PRD.md"
    if not path.is_file():
        return ""
    text = path.read_bytes().decode("utf-8", errors="surrogateescape")
    if not re.search(rf"(?m)^{re.escape(lines[0])}\s*$", text):
        nl = "\r\n" if "\r\n" in text else "\n"
        block = nl.join(lines) + nl + nl
        match = re.search(r"(?m)^## Directions\s*$", text)
        if match:
            text = text[:match.start()] + block + text[match.start():]
        else:
            text = text.rstrip("\r\n") + nl + nl + block.rstrip("\r\n") + nl
        path.write_bytes(text.encode("utf-8", errors="surrogateescape"))
        report["changed"].append("loc/PRD.md")
    return text


def step_2_to_3(project: Path, report: dict) -> None:
    text = add_section(project, report, DECISIONS)
    if not text:
        return
    section = re.search(r"(?ms)^## Decisions\s*$(.*?)(?=^## |\Z)", text).group(1)
    decided = re.search(r"(?m)^- D-\d+:", re.sub(r"(?s)<!--.*?-->", "", section))
    done = project / "loc" / "inbox" / "done"
    report["harvest"] = not decided and done.is_dir() and any(done.glob("*-plan-*.md"))


PRIORITIES = [
    "## Priorities",
    "<!-- Written only by the user: what matters most now. The `pm` agent orders the plans by it. Example:",
    "- Reliable import first, new reports later.",
    "-->",
]


def defer(path: Path, problem: str) -> str:
    """Turn an old plan into a deferred item: new name, type and one line; the text stays."""
    text = path.read_bytes().decode("utf-8", errors="surrogateescape")
    nl = "\r\n" if "\r\n" in text else "\n"
    line = f"**Deferred:** {date.today().isoformat()}: needs re-planning: {problem}"
    if re.search(r"(?m)^\*\*Type:\*\*", text):
        text = re.sub(r"(?m)^\*\*Type:\*\*[^\r\n]*", lambda _: "**Type:** deferred" + nl + line, text, count=1)
    else:
        head, _, rest = text.partition(nl)
        text = head + nl + nl + "**Type:** deferred" + nl + line + nl + rest
    new = path.name.replace("-plan-", "-deferred-", 1)
    path.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    path.rename(path.with_name(new))
    return new


def step_3_to_4(project: Path, report: dict) -> None:
    import check_plan
    import plan_queue
    add_section(project, report, PRIORITIES)
    if not (project / "loc" / "inbox").is_dir():
        return
    check_plan.PROJECT = project
    for plan in plan_queue.queue(project):
        if plan["group"] is not None or plan["running"]:
            continue
        path = project / plan["path"]
        problems = check_plan.own_issues(path)
        if problems:
            report["deferred"].append([path.name, defer(path, problems[0])])
    plan_queue.replace_references(project, report["deferred"])


STEPS = {1: step_1_to_2, 2: step_2_to_3, 3: step_3_to_4}


def migrate(project: Path) -> dict:
    loc = project / "loc"
    start = read_format(loc)
    report = {"project": project.as_posix(), "from": start, "to": start, "renamed": [], "changed": [],
              "translate": [], "harvest": False, "deferred": [], "regroup": False}
    if start is None:
        return report
    version = start
    while version < FORMAT:
        STEPS[version](project, report)
        version += 1
        (loc / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    report["to"] = version
    if (loc / "inbox").is_dir():
        import plan_queue
        report["regroup"] = any(plan["group"] is None and not plan["running"] for plan in plan_queue.queue(project))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
                        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)")
    args = parser.parse_args()
    print(json.dumps(migrate(args.project.resolve()), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
