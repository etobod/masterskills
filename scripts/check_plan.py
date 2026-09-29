#!/usr/bin/env python3
"""Mechanical gate for a plan file: no open questions, every milestone has a proof.

Checks, in order:
  - the required sections exist (Cel, Czego nie robimy, Kontekst z kodu,
    Kamienie milowe, Ryzyka i decyzje);
  - no forbidden phrase that marks an undecided plan ("do ustalenia", "TODO"...),
    outside inline code and outside the `## Bramka planu`, `## Uwagi z przeglądów`
    and `## Rozstrzygnięcie` sections, which record history rather than instructions;
  - no unfilled template placeholder such as `<co powstaje>`;
  - milestones (`### ` headings under `## Kamienie milowe`) and `**Dowód:**`
    lines are both counted, both > 0 and equal;
  - in a milestone with `**Kryteria:**`, every criterion
    `- K<n>[ (zachowanie)]: <what the code must do> → <test>` names its test in
    inline code, or `ręcznie` when the performer is the user;
  - `**Wykonawca:**`, when present, is `auto`, `agent`, or `użytkownik` with
    `(blokujący)` or `(odkładalny)`;
  - no expanded path of this plugin: a plan names plugin files as
    `${CLAUDE_PLUGIN_ROOT}/...`, so it still works on another machine.

Prints JSON {"plan", "ok", "milestones", "proofs", "issues": [{"line", "problem"}]}.
Exit code 0 when ok, 1 when there are issues, 2 when the file cannot be read.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

REQUIRED = ["Cel", "Czego nie robimy", "Kontekst z kodu", "Kamienie milowe", "Ryzyka i decyzje"]
HISTORY = {"Bramka planu", "Uwagi z przeglądów", "Rozstrzygnięcie"}
FORBIDDEN = [
    "do ustalenia", "do decyzji", "do rozstrzygnięcia", "do sprawdzenia", "sprawdzić, czy",
    "zobaczymy", "jeśli się okaże", "ewentualnie", "być może", "prawdopodobnie",
    "TODO", "TBD", "to be decided", "to be determined", "???",
]
PHRASE = re.compile(
    "|".join(r"(?<!\w)" + re.escape(p) + (r"(?!\w)" if p[-1].isalnum() else "") for p in FORBIDDEN),
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(
    r"<(co |nazwa|plik:linia|komenda|oczekiwany|ryzyko|opcjonalnie|świadomie|puste do)[^>]*>"
)
CODE = re.compile(r"`[^`]*`")
PROOF = re.compile(r"^\*\*Dowód:\*\*")
CRITERIA = re.compile(r"^\*\*Kryteria:\*\*\s*$")
CRITERION = re.compile(r"^- (K\d+)( \(zachowanie\))?: (?P<what>.+?)(?: → (?P<test>.*))?$")
PERFORMER = re.compile(r"^\*\*Wykonawca:\*\*\s*(?P<value>.*?)\s*$")
PERFORMERS = re.compile(r"^(auto|agent|użytkownik \((blokujący|odkładalny)\))$")
PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def plugin_roots() -> list:
    """Spellings of the plugin directory, normalised: `/` separators, lower case on Windows."""
    roots = {PLUGIN_ROOT.as_posix()}
    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        roots.add(os.environ["CLAUDE_PLUGIN_ROOT"].replace("\\", "/"))
    for root in list(roots):
        match = re.match(r"^([A-Za-z]):/(.*)$", root)
        if match:  # Git Bash spelling of a drive path
            roots.add(f"/{match.group(1)}/{match.group(2)}")
    return [normal(root.rstrip("/")) + "/" for root in roots]


def normal(text: str) -> str:
    text = text.replace("\\", "/")
    return text.lower() if os.name == "nt" else text


def check_milestone(name: str, criteria: list, performer, issues: list) -> None:
    """criteria: [(line number, text)]; performer: (line number, value) or None."""
    user = performer is not None and performer[1].startswith("użytkownik")
    if performer is not None and not PERFORMERS.match(performer[1]):
        issues.append({"line": performer[0], "problem": f"{name}: performer must be auto, agent, "
                       "użytkownik (blokujący) or użytkownik (odkładalny)"})
    for number, text in criteria:
        match = CRITERION.match(text)
        if not match:
            issues.append({"line": number, "problem": f"{name}: criterion must read "
                           "'- K<n>: <what the code must do> → `<test>`'"})
            continue
        test = (match.group("test") or "").strip()
        if test == "ręcznie" and user and not match.group(2):
            continue
        if not re.fullmatch(r"`[^`]+`", test):
            issues.append({"line": number, "problem": f"{name}: criterion {match.group(1)} has no test "
                           "(→ `<test file and name>`)"})


def check(text: str) -> dict:
    issues = []
    sections = set()
    section = None
    milestones = proofs = 0
    in_fence = False
    milestone, criteria, performer, in_criteria = None, [], None, False

    def close_milestone():
        if milestone:
            check_milestone(milestone, criteria, performer, issues)

    roots = plugin_roots()
    for number, line in enumerate(text.splitlines(), 1):
        if section not in HISTORY and any(root in normal(line) for root in roots):
            issues.append({"line": number, "problem": "plugin path in the plan: write it as "
                           "${CLAUDE_PLUGIN_ROOT}/..., so the plan works on another machine"})
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            close_milestone()
            milestone, criteria, performer, in_criteria = None, [], None, False
            section = line[3:].strip()
            sections.add(section)
            continue
        if section in HISTORY:
            continue
        if section == "Kamienie milowe" and line.startswith("### "):
            close_milestone()
            milestones += 1
            milestone, criteria, performer, in_criteria = f"M{milestones}", [], None, False
        elif milestone and CRITERIA.match(line):
            in_criteria = True
        elif milestone and in_criteria and line.startswith("- "):
            criteria.append((number, line))
        elif milestone and PERFORMER.match(line):
            performer = (number, PERFORMER.match(line).group("value"))
            in_criteria = False
        elif line.strip():
            in_criteria = False
        if PROOF.match(line):
            proofs += 1

        prose = CODE.sub("", line)
        for match in PHRASE.finditer(prose):
            issues.append({"line": number, "problem": f"undecided phrase: {match.group(0)!r}"})
        for match in PLACEHOLDER.finditer(prose):
            issues.append({"line": number, "problem": f"unfilled placeholder: {match.group(0)}"})

    close_milestone()
    for name in REQUIRED:
        if name not in sections:
            issues.append({"line": 0, "problem": f"missing section: ## {name}"})
    if milestones == 0:
        issues.append({"line": 0, "problem": "no milestones (### headings under ## Kamienie milowe)"})
    if proofs == 0:
        issues.append({"line": 0, "problem": "no **Dowód:** lines"})
    if milestones != proofs:
        issues.append({"line": 0, "problem": f"{milestones} milestones but {proofs} proofs"})

    return {"ok": not issues, "milestones": milestones, "proofs": proofs, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan", type=Path, help="plan file, e.g. loc/inbox/007-plan-csv-export.md")
    args = parser.parse_args()
    try:
        text = args.plan.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(json.dumps({"plan": args.plan.as_posix(), "ok": False, "error": str(error)}))
        return 2
    result = check(text)
    print(json.dumps({"plan": args.plan.as_posix(), **result}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
