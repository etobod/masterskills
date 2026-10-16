#!/usr/bin/env python3
"""Mechanical gate for a plan file: no open questions, every milestone has a proof.

Checks, in order:
  - the required sections exist (Cel, Czego nie robimy, Nie bronimy przed,
    Kontekst z kodu, Kamienie milowe, Ryzyka i decyzje), and `Nie bronimy przed`
    has at least one `- ` line (`- brak` when the code defends against everything);
  - no forbidden phrase that marks an undecided plan ("do ustalenia", "TODO"...),
    outside inline code and outside the `## Bramka planu`, `## Uwagi z przeglądów`, `## Fragment PRD`
    and `## Rozstrzygnięcie` sections, which record history rather than instructions;
  - no unfilled template placeholder such as `<co powstaje>`;
  - milestones (`### ` headings under `## Kamienie milowe`) and `**Dowód:**`
    lines are both counted, both > 0 and equal;
  - in a milestone with `**Kryteria:**`, every criterion
    `- K<n>[ (zachowanie)]: <what the code must do> → <test>` names its test in
    inline code, or `ręcznie` when the performer is the user;
  - every milestone has `**Kryteria:**` or `**Bez testów:** <reason>`, unless it
    sets up the test suite (names `TEST-PLAN.md`) or the user performs it;
  - in a project without `loc/TEST-PLAN.md` ($CLAUDE_PROJECT_DIR, else the
    current directory), a plan with criteria sets up the suite in M1;
  - `**Wykonawca:**`, when present, is `auto`, `agent`, or `użytkownik` with
    `(blokujący)` or `(odkładalny)`;
  - a criterion's test is not a shell check (`grep`, `test -f`, `open`...);
  - an automatic proof reads `` `<command>` → `<output>` `` and does not just
    open a file;
  - with `--ready` (before execution): `## Bramka planu` records a round, and
    the input file named in `**Źródło:**` is no longer open in `loc/inbox/`;
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

REQUIRED = ["Cel", "Czego nie robimy", "Nie bronimy przed", "Kontekst z kodu", "Kamienie milowe", "Ryzyka i decyzje"]
DEFENCE = "Nie bronimy przed"
HISTORY = {"Bramka planu", "Uwagi z przeglądów", "Fragment PRD", "Rozstrzygnięcie"}
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
    r"<(co |kto albo|nazwa|plik:linia|komenda|oczekiwany|ryzyko|opcjonalnie|świadomie|puste do)[^>]*>"
)
CODE = re.compile(r"`[^`]*`")
PROOF = re.compile(r"^\*\*Dowód:\*\*")
CRITERIA = re.compile(r"^\*\*Kryteria:\*\*\s*$")
CRITERION = re.compile(r"^- (K\d+)( \(zachowanie\))?: (?P<what>.+?)(?: → (?P<test>.*))?$")
PERFORMER = re.compile(r"^\*\*Wykonawca:\*\*\s*(?P<value>.*?)\s*$")
PERFORMERS = re.compile(r"^(auto|agent|użytkownik \((blokujący|odkładalny)\))$")
NO_TESTS = re.compile(r"^\*\*Bez testów:\*\*\s*(?P<reason>.*?)\s*$")
SUITE = "TEST-PLAN.md"
# A criterion's "test" that is really a shell check: it proves a word or a file exists, not behaviour.
SHELL_CHECK = re.compile(r"^`\s*(grep|test|open|start|xdg-open|ls|cat|find|echo|wc|type|dir|curl)\b|&&|\|\||[|;]")
CHECKABLE_PROOF = re.compile(r"^\*\*Dowód:\*\*\s*`(?P<command>[^`]+)`\s*→\s*`[^`]+`")
BROWSER = re.compile(r"^\s*(open|start|xdg-open)\b")
GATE_RECORD = "Bramka planu"
INPUT = re.compile(r"\b\d{3,}-(brainstorm|przeglad|odlozone|utknelo|pytanie)-[^\s`/\\)]+\.md\b")
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


def check_milestone(name: str, criteria: list, performer, issues: list, tested: dict) -> None:
    """criteria: [(line number, text)]; performer: (line number, value) or None;
    tested: {"criteria", "no_tests" (reason or None), "suite"} seen in the milestone."""
    user = performer is not None and performer[1].startswith("użytkownik")
    if tested["no_tests"] == "":
        issues.append({"line": 0, "problem": f"{name}: **Bez testów:** needs a reason, e.g. 'tylko dokumenty'"})
    elif not (tested["criteria"] or tested["no_tests"] or tested["suite"] or user):
        issues.append({"line": 0, "problem": f"{name}: no **Kryteria:** (with tests) and no "
                       "**Bez testów:** <reason>; a milestone that changes code needs criteria"})
    proof = tested.get("proof")
    automatic = performer is None or performer[1] == "auto"
    if proof and automatic:
        match = CHECKABLE_PROOF.match(proof[1])
        if not match:
            issues.append({"line": proof[0], "problem": f"{name}: an automatic proof reads "
                           "'**Dowód:** `<command>` → `<expected output>`'; a result you only see "
                           "needs **Wykonawca:** użytkownik (blokujący) or (odkładalny)"})
        elif BROWSER.match(match.group("command")):
            issues.append({"line": proof[0], "problem": f"{name}: the proof only opens a file; "
                           "run a test command, or make the user the performer"})
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
        elif SHELL_CHECK.search(test):
            issues.append({"line": number, "problem": f"{name}: criterion {match.group(1)}: {test} is a shell "
                           "check, not a test; name a test that checks the behaviour (`test_app.py::test_polish`)"})


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def check_ready(text: str, issues: list) -> None:
    """Planning finished: the gate is recorded and the input file is closed."""
    section, record = None, []
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif section == GATE_RECORD and line.strip() and not re.match(r"^\s*(<.*>|<!--.*-->)\s*$", line):
            record.append(line)
    if not record:
        issues.append({"line": 0, "problem": f"## {GATE_RECORD} records no round: the plan never went "
                       "through the loc-planning gate; run loc-planning on it"})
    source = re.search(r"^\*\*Źródło:\*\*(.*)$", text, re.MULTILINE)
    for match in INPUT.finditer(source.group(1) if source else ""):
        if (project_dir() / "loc" / "inbox" / match.group(0)).is_file():
            issues.append({"line": 0, "problem": f"input loc/inbox/{match.group(0)} is still open: loc-planning "
                           "did not close it (its step 6, references/closing.md); run loc-planning on the plan"})


def check(text: str) -> dict:
    issues = []
    sections = set()
    defended = 0
    section = None
    milestones = proofs = 0
    in_fence = False
    milestone, criteria, performer, in_criteria = None, [], None, False
    tested = {}
    any_criteria = first_sets_up_suite = False

    def close_milestone():
        if milestone:
            check_milestone(milestone, criteria, performer, issues, tested)

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
        if section == DEFENCE and line.startswith("- "):
            defended += 1
        if section == "Kamienie milowe" and line.startswith("### "):
            close_milestone()
            milestones += 1
            milestone, criteria, performer, in_criteria = f"M{milestones}", [], None, False
            tested = {"criteria": False, "no_tests": None, "suite": SUITE in line}
        elif milestone and CRITERIA.match(line):
            in_criteria = True
            tested["criteria"] = any_criteria = True
        elif milestone and NO_TESTS.match(line):
            tested["no_tests"] = NO_TESTS.match(line).group("reason")
            in_criteria = False
        elif milestone and in_criteria and line.startswith("- "):
            criteria.append((number, line))
        elif milestone and PERFORMER.match(line):
            performer = (number, PERFORMER.match(line).group("value"))
            in_criteria = False
        elif line.strip():
            in_criteria = False
        if milestone and SUITE in line:
            tested["suite"] = True
            first_sets_up_suite = first_sets_up_suite or milestone == "M1"
        if PROOF.match(line):
            proofs += 1
            if milestone:
                tested["proof"] = (number, line)

        prose = CODE.sub("", line)
        for match in PHRASE.finditer(prose):
            issues.append({"line": number, "problem": f"undecided phrase: {match.group(0)!r}"})
        for match in PLACEHOLDER.finditer(prose):
            issues.append({"line": number, "problem": f"unfilled placeholder: {match.group(0)}"})

    close_milestone()
    for name in REQUIRED:
        if name not in sections:
            issues.append({"line": 0, "problem": f"missing section: ## {name}"})
    if DEFENCE in sections and defended == 0:
        issues.append({"line": 0, "problem": f"empty section: ## {DEFENCE} (write `- brak` when nothing)"})
    if milestones == 0:
        issues.append({"line": 0, "problem": "no milestones (### headings under ## Kamienie milowe)"})
    if proofs == 0:
        issues.append({"line": 0, "problem": "no **Dowód:** lines"})
    if milestones != proofs:
        issues.append({"line": 0, "problem": f"{milestones} milestones but {proofs} proofs"})
    project = project_dir()
    if any_criteria and not first_sets_up_suite and not (project / "loc" / SUITE).is_file():
        issues.append({"line": 0, "problem": "the project has no loc/TEST-PLAN.md: M1 must set up the "
                       "test suite (framework, test command in CLAUDE.md Commands, smoke test, loc/TEST-PLAN.md)"})

    return {"ok": not issues, "milestones": milestones, "proofs": proofs, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan", type=Path, help="plan file, e.g. loc/inbox/007-plan-csv-export.md")
    parser.add_argument("--ready", action="store_true",
                        help="before execution: also require a recorded gate and a closed input file")
    args = parser.parse_args()
    try:
        text = args.plan.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(json.dumps({"plan": args.plan.as_posix(), "ok": False, "error": str(error)}))
        return 2
    result = check(text)
    if args.ready:
        check_ready(text, result["issues"])
        result["ok"] = not result["issues"]
    print(json.dumps({"plan": args.plan.as_posix(), **result}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
