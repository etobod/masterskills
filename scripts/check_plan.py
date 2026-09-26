#!/usr/bin/env python3
"""Mechanical gate for a plan file: no open questions, every milestone has a proof.

Checks, in order:
  - the required sections exist (Cel, Czego nie robimy, Kontekst z kodu,
    Kamienie milowe, Ryzyka i decyzje);
  - no forbidden phrase that marks an undecided plan ("do ustalenia", "TODO"...),
    outside inline code and outside the `## Bramka planu` and `## Rozstrzygnięcie`
    sections, which record history rather than instructions;
  - no unfilled template placeholder such as `<co powstaje>`;
  - milestones (`### ` headings under `## Kamienie milowe`) and `**Dowód:**`
    lines are both counted, both > 0 and equal.

Prints JSON {"plan", "ok", "milestones", "proofs", "issues": [{"line", "problem"}]}.
Exit code 0 when ok, 1 when there are issues, 2 when the file cannot be read.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = ["Cel", "Czego nie robimy", "Kontekst z kodu", "Kamienie milowe", "Ryzyka i decyzje"]
HISTORY = {"Bramka planu", "Rozstrzygnięcie"}
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


def check(text: str) -> dict:
    issues = []
    sections = set()
    section = None
    milestones = proofs = 0
    in_fence = False

    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            section = line[3:].strip()
            sections.add(section)
            continue
        if section in HISTORY:
            continue
        if section == "Kamienie milowe" and line.startswith("### "):
            milestones += 1
        if PROOF.match(line):
            proofs += 1

        prose = CODE.sub("", line)
        for match in PHRASE.finditer(prose):
            issues.append({"line": number, "problem": f"undecided phrase: {match.group(0)!r}"})
        for match in PLACEHOLDER.finditer(prose):
            issues.append({"line": number, "problem": f"unfilled placeholder: {match.group(0)}"})

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
    parser.add_argument("plan", type=Path, help="plan file, e.g. inbox/007-plan-csv-export.md")
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
