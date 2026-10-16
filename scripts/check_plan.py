#!/usr/bin/env python3
"""Mechanical gate for a plan file: no open questions, every milestone has a proof.

Checks, in order:
  - the required sections exist (Goal, Out of scope, Not defended against,
    Code context, Milestones, Risks and decisions), and `Not defended against`
    has at least one `- ` line (`- none` when the code defends against everything);
  - no forbidden phrase that marks an undecided plan ("do ustalenia", "TODO"...),
    outside inline code and outside the `## Plan gate`, `## Review notes`, `## PRD fragment`
    and `## Resolution` sections, which record history rather than instructions;
  - no unfilled template placeholder such as `<co powstaje>`;
  - milestones (`### ` headings under `## Milestones`) and `**Proof:**`
    lines are both counted, both > 0 and equal;
  - in a milestone with `**Criteria:**`, every criterion
    `- K<n>[ (behaviour)]: <what the code must do> → <test>` names its test in
    inline code, or `manual` when the performer is the user;
  - every milestone has `**Criteria:**` or `**No tests:** <reason>`, unless it
    sets up the test suite (names `TEST-PLAN.md`) or the user performs it;
  - in a project without a test suite ($CLAUDE_PROJECT_DIR, else the current
    directory), a plan with criteria sets up the suite in M1; the suite is
    `loc/TEST-PLAN.md` plus a test command (`test` or `spec`) in `CLAUDE.md`
    `## Commands`, since a stub file alone proves nothing runs;
  - `**Performer:**`, when present, is `auto`, `agent`, or `user` with
    `(blocking)` or `(deferrable)`;
  - a criterion's test is not a shell check (`grep`, `test -f`, `open`...) and
    names a test (`test` or `spec` in it), not a source file;
  - an automatic proof reads `` `<command>` → `<output>` `` and does not just
    open a file;
  - a plan whose `**Source:**` names a `review` (in `loc/inbox/` or `done/`)
    accounts for each of its findings (`NNN #n`, numbered in `## Findings`
    order): Blocking and Non-blocking ones in a milestone (the judge's `fix`)
    or an `enough` line in `## Review notes`; Suggestion and Unrealistic ones
    only in `## Review notes`; either may instead be under the review's
    `## Resolution` when already fixed;
  - with `--ready` (before execution): `## Plan gate` records a round, and
    the input file named in `**Source:**` is no longer open in `loc/inbox/`;
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

REQUIRED = ["Goal", "Out of scope", "Not defended against", "Code context", "Milestones", "Risks and decisions"]
DEFENCE = "Not defended against"
HISTORY = {"Plan gate", "Review notes", "PRD fragment", "Resolution"}
FORBIDDEN = [
    "do ustalenia", "do decyzji", "do rozstrzygnięcia", "do sprawdzenia", "sprawdzić, czy",
    "zobaczymy", "jeśli się okaże", "ewentualnie", "być może", "prawdopodobnie",
    "TODO", "TBD", "to be decided", "to be determined", "to be confirmed", "to be checked", "we will see",
    "if it turns out", "maybe", "perhaps", "probably", "???",
]
PHRASE = re.compile(
    "|".join(r"(?<!\w)" + re.escape(p) + (r"(?!\w)" if p[-1].isalnum() else "") for p in FORBIDDEN),
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(
    r"<(what |who or what|name|file:line|command|expected|a risk|optional|deliberately|empty until|test file)[^>]*>"
)
CODE = re.compile(r"`[^`]*`")
COMMENT = re.compile(r"<!--.*?-->", re.S)
PROOF = re.compile(r"^\*\*Proof:\*\*")
CRITERIA = re.compile(r"^\*\*Criteria:\*\*\s*$")
CRITERION = re.compile(r"^- (K\d+)( \(behaviour\))?: (?P<what>.+?)(?: → (?P<test>.*))?$")
PERFORMER = re.compile(r"^\*\*Performer:\*\*\s*(?P<value>.*?)\s*$")
PERFORMERS = re.compile(r"^(auto|agent|user \((blocking|deferrable)\))$")
NO_TESTS = re.compile(r"^\*\*No tests:\*\*\s*(?P<reason>.*?)\s*$")
SUITE = "TEST-PLAN.md"
# A criterion's "test" that is really a shell check: it proves a word or a file exists, not behaviour.
SHELL_CHECK = re.compile(r"^`\s*(grep|test|open|start|xdg-open|ls|cat|find|echo|wc|type|dir|curl)\b|&&|\|\||[|;]")
# A criterion names a test: test frameworks put "test" or "spec" in file or test names.
TEST_NAME = re.compile(r"test|spec", re.I)
# A command and an arrow, but the expected result written as prose.
PROSE_RESULT = re.compile(r"^\*\*Proof:\*\*\s*`[^`]+`\s*→\s*(?P<result>[^`\s][^`]*?)\s*$")
CHECKABLE_PROOF = re.compile(r"^\*\*Proof:\*\*\s*`(?P<command>[^`]+)`\s*→\s*`[^`]+`")
BROWSER = re.compile(r"^\s*(open|start|xdg-open)\b")
GATE_RECORD = "Plan gate"
FINDING = re.compile(r"^- \*\*\[([^\]]+)\]\*\*")
NO_JUDGE = {"suggestion", "unrealistic", "low"}
INPUT = re.compile(r"\b\d{3,}-(brainstorm|review|deferred|stuck|question)-[^\s`/\\)]+\.md\b")
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


PATH_END = re.compile(r"[\s`'\")\]]")
ROOT_VAR = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`'\")\]]+)")


def exists(rest: str) -> bool:
    """OpenCode installs skills next to the plugin directory, not inside it."""
    return (PLUGIN_ROOT / rest).exists() or (rest.startswith("skills/") and (PLUGIN_ROOT.parent / rest).exists())


def in_plugin(rest: str) -> str:
    """The shortest tail of `rest` that exists in the plugin, or `rest` itself."""
    parts = rest.rstrip(".,;:").split("/")
    for start in range(len(parts)):
        tail = "/".join(parts[start:])
        if tail and exists(tail):
            return tail
    return rest.rstrip(".,;:")


def plugin_path_problems(line: str, roots: list) -> list:
    """An expanded plugin path, or a `${CLAUDE_PLUGIN_ROOT}/...` path that does not exist.

    Each message gives the exact path to write: a weak model told only to
    "write it as ${CLAUDE_PLUGIN_ROOT}/..." replaced the wrong prefix.
    """
    problems, low = [], normal(line)
    for root in roots:
        at = low.find(root)
        if at >= 0:
            rest = PATH_END.split(line[at + len(root):].replace("\\", "/"), 1)[0]
            problems.append("plugin path in the plan: write `${CLAUDE_PLUGIN_ROOT}/" + in_plugin(rest)
                            + "`, so the plan works on another machine")
            return problems
    for match in ROOT_VAR.finditer(line):
        rest = match.group(1).rstrip(".,;:")
        if any(c in rest for c in "<*{") or exists(rest):
            continue
        fixed = in_plugin(rest)
        hint = f": write `${{CLAUDE_PLUGIN_ROOT}}/{fixed}`" if fixed != rest else ""
        problems.append(f"${{CLAUDE_PLUGIN_ROOT}}/{rest} does not exist in the plugin{hint}")
    return problems


def normal(text: str) -> str:
    text = text.replace("\\", "/")
    return text.lower() if os.name == "nt" else text


def check_milestone(name: str, criteria: list, performer, issues: list, tested: dict) -> None:
    """criteria: [(line number, text)]; performer: (line number, value) or None;
    tested: {"criteria", "no_tests" (reason or None), "suite"} seen in the milestone."""
    user = performer is not None and performer[1].startswith("user")
    if tested["no_tests"] == "":
        issues.append({"line": 0, "problem": f"{name}: **No tests:** needs a reason, e.g. 'documents only'"})
    elif not (tested["criteria"] or tested["no_tests"] or tested["suite"] or user):
        issues.append({"line": 0, "problem": f"{name}: no **Criteria:** (with tests) and no "
                       "**No tests:** <reason>; a milestone that changes code needs criteria"})
    proof = tested.get("proof")
    automatic = performer is None or performer[1] == "auto"
    if proof and automatic:
        match = CHECKABLE_PROOF.match(proof[1])
        prose = PROSE_RESULT.match(proof[1])
        if prose:
            issues.append({"line": proof[0], "problem": f"{name}: after → give the exact output of the "
                           f"command in backticks, '`<command>` → `<exact output>`' (e.g. `2`, `OK`); "
                           f"found: '{prose.group('result')}'"})
        elif not match:
            issues.append({"line": proof[0], "problem": f"{name}: an automatic proof reads "
                           "'**Proof:** `<command>` → `<expected output>`'; a result you only see "
                           "needs **Performer:** user (blocking) or (deferrable)"})
        elif BROWSER.match(match.group("command")):
            issues.append({"line": proof[0], "problem": f"{name}: the proof only opens a file; "
                           "run a test command, or make the user the performer"})
    if performer is not None and not PERFORMERS.match(performer[1]):
        issues.append({"line": performer[0], "problem": f"{name}: performer must be auto, agent, "
                       "user (blocking) or user (deferrable)"})
    for number, text in criteria:
        match = CRITERION.match(text)
        if not match:
            issues.append({"line": number, "problem": f"{name}: criterion must read "
                           "'- K<n>: <what the code must do> → `<test>`'"})
            continue
        test = (match.group("test") or "").strip()
        if test == "manual" and user and not match.group(2):
            continue
        if not re.fullmatch(r"`[^`]+`", test):
            issues.append({"line": number, "problem": f"{name}: criterion {match.group(1)} has no test "
                           "(→ `<test file and name>`)"})
        elif SHELL_CHECK.search(test):
            issues.append({"line": number, "problem": f"{name}: criterion {match.group(1)}: {test} is a shell "
                           "check, not a test; name a test that checks the behaviour (`test_app.py::test_polish`)"})
        elif not TEST_NAME.search(test):
            issues.append({"line": number, "problem": f"{name}: criterion {match.group(1)}: {test} names no "
                           "test; give the test file and the test's name (`tests/app.test.js::polish greeting`)"})


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def has_suite(project: Path) -> bool:
    """A test suite is `loc/TEST-PLAN.md` plus a test command in `CLAUDE.md` `## Commands`:
    the file alone can be written in a minute and proves nothing runs."""
    if not (project / "loc" / SUITE).is_file():
        return False
    try:
        text = (project / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    section = re.search(r"(?ms)^## Commands\s*?$(.*?)(?=^## |\Z)", text)
    body = COMMENT.sub("", section.group(1)) if section else ""
    return any(TEST_NAME.search(line) for line in body.splitlines())


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
    source = re.search(r"^\*\*Source:\*\*(.*)$", text, re.MULTILINE)
    for match in INPUT.finditer(source.group(1) if source else ""):
        if (project_dir() / "loc" / "inbox" / match.group(0)).is_file():
            issues.append({"line": 0, "problem": f"input loc/inbox/{match.group(0)} is still open: loc-planning "
                           "did not close it (its step 7); run loc-planning on the plan"})


def sections_of(text: str) -> dict:
    """`## ` heading -> its lines."""
    result, section = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            result.setdefault(section, [])
        elif section:
            result[section].append(line)
    return result


def find_input(name: str):
    for folder in ("inbox", "inbox/done"):
        path = project_dir() / "loc" / folder / name
        if path.is_file():
            return path
    return None


def check_review(text: str, issues: list) -> None:
    """A plan made from a review accounts for every finding of it: the judge's `fix` in a milestone,
    its `enough` (or a suggestion, unrealistic) line in `## Review notes`, or `## Resolution` of the
    review for one already fixed. A finding that needs no judge never goes into a milestone."""
    source = re.search(r"^\*\*Source:\*\*(.*)$", text, re.MULTILINE)
    plan = sections_of(text)
    milestones = "\n".join(plan.get("Milestones", []))
    notes = plan.get("Review notes", [])
    for match in INPUT.finditer(source.group(1) if source else ""):
        path = find_input(match.group(0)) if match.group(1) == "review" else None
        if not path:
            continue
        number = match.group(0).split("-", 1)[0]
        review = sections_of(path.read_text(encoding="utf-8", errors="replace"))
        resolution = "\n".join(review.get("Resolution", []))
        findings = [line for line in review.get("Findings", []) if line.startswith("- ")]
        for index, line in enumerate(findings, 1):
            ref = f"{number} #{index}"
            cited = re.compile(rf"\b{re.escape(ref)}(?!\d)")
            category = FINDING.match(line)
            category = category.group(1).strip() if category else "Non-blocking"
            judged = category.lower() not in NO_JUDGE
            in_milestone = bool(cited.search(milestones))
            noted = [note for note in notes if cited.search(note)]
            if not judged and in_milestone:
                issues.append({"line": 0, "problem": f"review {ref} is a {category}: it never goes into a "
                               f"milestone; record it in ## Review notes as `- {category.lower()} (planning): "
                               f"{ref} …`"})
            elif not (in_milestone or noted or cited.search(resolution)):
                issues.append({"line": 0, "problem": (
                    f"review {ref} ({category}) is not accounted for: give the Blocking and Non-blocking "
                    f"findings of {match.group(0)} to the judge agent; `fix` → a milestone citing {ref}, "
                    f"`enough` → `- enough (planning): {ref} … Reason: …` in ## Review notes"
                    if judged else
                    f"review {ref} ({category}) is not accounted for: record it in ## Review notes as "
                    f"`- {category.lower()} (planning): {ref} …`")})


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
        if section not in HISTORY:
            for problem in plugin_path_problems(line, roots):
                issues.append({"line": number, "problem": problem})
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
        if section == "Milestones" and line.startswith("### "):
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
        issues.append({"line": 0, "problem": f"empty section: ## {DEFENCE} (write `- none` when nothing)"})
    if milestones == 0:
        issues.append({"line": 0, "problem": "no milestones (### headings under ## Milestones)"})
    if proofs == 0:
        issues.append({"line": 0, "problem": "no **Proof:** lines"})
    if milestones != proofs:
        issues.append({"line": 0, "problem": f"{milestones} milestones but {proofs} proofs"})
    project = project_dir()
    if any_criteria and not first_sets_up_suite and not has_suite(project):
        issues.append({"line": 0, "problem": "the project has no test suite (loc/TEST-PLAN.md and a test "
                       "command in CLAUDE.md Commands): M1 must set up the test suite (framework, test command "
                       "in CLAUDE.md Commands, smoke test, loc/TEST-PLAN.md); do not create loc/TEST-PLAN.md "
                       "while planning, M1 creates it"})

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
    check_review(text, result["issues"])
    result["ok"] = not result["issues"]
    if args.ready:
        check_ready(text, result["issues"])
        result["ok"] = not result["issues"]
    print(json.dumps({"plan": args.plan.as_posix(), **result}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
