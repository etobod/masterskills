#!/usr/bin/env python3
"""Validate a plan execution state file, `loc/state/<NNN>.json`.

`loc-orchestrate` writes the file after every step, so a new session (after
/clear or compaction) resumes from it without asking. Schema, all keys required:

    {
      "plan": "loc/inbox/018-plan-csv-export.md",   # or loc/inbox/done/..., NNN = file name
      "mode": "inline" | "subagent",
      "milestone": 1,                            # current one, 1-based
      "phase": "start" | "implement" | "proof" | "code-review"
               | "qa" | "final-review" | "journal" | "done",
      "milestones": [
        {"id": "M1", "status": "pending" | "in_progress" | "done" | "stuck",
         "start": "<snapshot hash>" | null, "end": "<snapshot hash>" | null}
      ],
      "gates": {                                 # "M1/red", "M1/proof", "M1/code-review", "qa", "final-review"
        "M1/red": {"rounds": 1, "passed": true, "stuck": null, "output": "AssertionError: ...",
                   "test_author": true},
        "M1/proof": {"rounds": 3, "passed": false, "stuck": "loc/inbox/004-utknelo-....md"}
      },
      "deviations": [{"milestone": "M1", "rule": 1-4, "note": "...",
                      "question": "loc/inbox/NNN-pytanie-....md"}],   # question: rule 4 only
      "next_action": "exactly what to do next",
      "updated": "YYYY-MM-DD HH:MM",
      "deferred": "loc/inbox/NNN-odlozone-....md" | null   # optional
    }

Gate rules: at most 3 rounds; a gate that used 3 rounds without passing names its
`utknelo` file, and that file must exist in `loc/inbox/` or `loc/inbox/done/`.
A passed `M<n>/red` gate (the new tests failed before the code) keeps the
failing test output in `output`; when the plan's milestone has a
`(zachowanie)` criterion it also says whether the `test-author` agent wrote
those tests (`test_author: true`), and `false` needs a deviation for that
milestone explaining why. A plan with `**Kryteria:**` reaches `journal`
or `done` only after a `qa` gate that passed or went stuck. `deferred`, when
set, names the plan's `odlozone` file (review Suggestions), which must exist in
`loc/inbox/` or `loc/inbox/done/`.

Prints JSON {"state", "ok", "problems": [...]}. Exit 0 when valid, 1 when not,
2 when the file cannot be read or is not JSON.
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

KEYS = {"plan", "mode", "milestone", "phase", "milestones", "gates", "deviations",
        "next_action", "updated"}
OPTIONAL = {"deferred"}
MODES = {"inline", "subagent"}
PHASES = {"start", "implement", "proof", "code-review", "qa", "final-review", "journal", "done"}
STATUSES = {"pending", "in_progress", "done", "stuck"}
MAX_ROUNDS = 3
PLAN = re.compile(r"^loc/inbox/(done/)?(\d{3,})-plan-[^/]+\.md$")
GATE = re.compile(r"^(M\d+)/(red|proof|code-review)$|^(qa|final-review)$")
STUCK = re.compile(r"^loc/inbox/(done/)?\d{3,}-utknelo-[^/]+\.md$")
DEFERRED = re.compile(r"^loc/inbox/(done/)?\d{3,}-odlozone-[^/]+\.md$")
QUESTION = re.compile(r"^loc/inbox/(done/)?\d{3,}-pytanie-[^/]+\.md$")
HASH = re.compile(r"^[0-9a-f]{7,40}$")
BEHAVIOUR = re.compile(r"^- K\d+ \(zachowanie\):")


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def check_milestones(data: dict, problems: list) -> list:
    items = data.get("milestones")
    if not isinstance(items, list) or not items:
        problems.append("milestones: expected a non-empty list")
        return []
    ids = []
    for index, item in enumerate(items, 1):
        where = f"milestones[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{where}: expected an object")
            continue
        if item.get("id") != f"M{index}":
            problems.append(f"{where}.id: expected 'M{index}', got {item.get('id')!r}")
        if item.get("status") not in STATUSES:
            problems.append(f"{where}.status: expected one of {sorted(STATUSES)}")
        for point in ("start", "end"):
            value = item.get(point, "missing")
            if value is not None and not (isinstance(value, str) and HASH.match(value)):
                problems.append(f"{where}.{point}: expected a snapshot hash or null")
        if item.get("status") == "done" and not (item.get("start") and item.get("end")):
            problems.append(f"{where}: done without start and end snapshots")
        ids.append(f"M{index}")
    return ids


def check_gates(data: dict, ids: list, project: Path, problems: list) -> None:
    gates = data.get("gates")
    if not isinstance(gates, dict):
        problems.append("gates: expected an object")
        return
    for name, gate in gates.items():
        match = GATE.match(name)
        if not match:
            problems.append(f"gates: unknown gate {name!r} (M<n>/red, M<n>/proof, M<n>/code-review, qa, final-review)")
            continue
        if match.group(1) and match.group(1) not in ids:
            problems.append(f"gates.{name}: no such milestone")
        if not isinstance(gate, dict):
            problems.append(f"gates.{name}: expected an object")
            continue
        rounds, passed, stuck = gate.get("rounds"), gate.get("passed"), gate.get("stuck")
        if not is_int(rounds) or rounds < 0:
            problems.append(f"gates.{name}.rounds: expected an integer >= 0")
            continue
        if not isinstance(passed, bool):
            problems.append(f"gates.{name}.passed: expected true or false")
        if rounds > MAX_ROUNDS:
            problems.append(f"gates.{name}: {rounds} rounds, the limit is {MAX_ROUNDS}")
        if rounds == MAX_ROUNDS and passed is False:
            if not (isinstance(stuck, str) and STUCK.match(stuck)):
                problems.append(f"gates.{name}: {MAX_ROUNDS} failed rounds without a utknelo file")
            elif not any((project / p).is_file() for p in (stuck, stuck.replace("loc/inbox/", "loc/inbox/done/", 1))):
                problems.append(f"gates.{name}.stuck: {stuck} does not exist")
        elif stuck is not None:
            problems.append(f"gates.{name}.stuck: only a gate that failed {MAX_ROUNDS} rounds has one")
        output = gate.get("output")
        if match.group(2) == "red" and passed is True and not (isinstance(output, str) and output.strip()):
            problems.append(f"gates.{name}.output: a passed red gate keeps the failing test output")


def plan_text(project: Path, plan) -> str:
    for rel in (str(plan), str(plan).replace("loc/inbox/done/", "loc/inbox/", 1),
                str(plan).replace("loc/inbox/", "loc/inbox/done/", 1)):
        try:
            return (project / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return ""


def has_criteria(project: Path, plan) -> bool:
    return re.search(r"^\*\*Kryteria:\*\*", plan_text(project, plan), re.MULTILINE) is not None


def behaviour_milestones(project: Path, plan) -> set:
    """Milestones (M1, M2...) of the plan with a `(zachowanie)` criterion."""
    found, section, number = set(), None, 0
    for line in plan_text(project, plan).splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif section == "Kamienie milowe" and line.startswith("### "):
            number += 1
        elif number and section == "Kamienie milowe" and BEHAVIOUR.match(line):
            found.add(f"M{number}")
    return found


def check_test_author(data: dict, project: Path, problems: list) -> None:
    gates = data.get("gates")
    if not isinstance(gates, dict):
        return
    deviated = {item.get("milestone") for item in data.get("deviations") or [] if isinstance(item, dict)}
    for milestone in sorted(behaviour_milestones(project, data.get("plan"))):
        gate = gates.get(f"{milestone}/red")
        if not (isinstance(gate, dict) and gate.get("passed") is True):
            continue
        author = gate.get("test_author")
        if author is False and milestone not in deviated:
            problems.append(f"gates.{milestone}/red.test_author: false needs a deviation for {milestone} "
                            "saying why test-author did not write the (zachowanie) tests")
        elif author is not True and author is not False:
            problems.append(f"gates.{milestone}/red.test_author: {milestone} has a (zachowanie) criterion; "
                            "expected true (test-author wrote its tests) or false with a deviation")


def exists_in_inbox(project: Path, rel: str) -> bool:
    return any((project / p).is_file() for p in (rel, rel.replace("loc/inbox/", "loc/inbox/done/", 1),
                                                   rel.replace("loc/inbox/done/", "loc/inbox/", 1)))


def check_deferred(data: dict, project: Path, problems: list) -> None:
    deferred = data.get("deferred")
    if deferred is None:
        return
    if not (isinstance(deferred, str) and DEFERRED.match(deferred)):
        problems.append("deferred: expected null or loc/inbox/NNN-odlozone-<topic>.md")
    elif not exists_in_inbox(project, deferred):
        problems.append(f"deferred: {deferred} does not exist")


def check_qa(data: dict, project: Path, problems: list) -> None:
    if data.get("phase") not in ("journal", "done") or not has_criteria(project, data.get("plan")):
        return
    gate = (data.get("gates") or {}).get("qa")
    if not (isinstance(gate, dict) and (gate.get("passed") is True or gate.get("stuck"))):
        problems.append("gates.qa: a plan with **Kryteria:** needs a qa gate that passed or went stuck "
                        "before journal")


def check_deviations(data: dict, ids: list, problems: list) -> None:
    items = data.get("deviations")
    if not isinstance(items, list):
        problems.append("deviations: expected a list")
        return
    for index, item in enumerate(items, 1):
        where = f"deviations[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{where}: expected an object")
            continue
        if item.get("milestone") not in ids:
            problems.append(f"{where}.milestone: expected one of {ids}")
        rule = item.get("rule")
        if not is_int(rule) or not 1 <= rule <= 4:
            problems.append(f"{where}.rule: expected 1-4")
        if not (isinstance(item.get("note"), str) and item["note"].strip()):
            problems.append(f"{where}.note: expected text")
        if rule == 4 and not (isinstance(item.get("question"), str) and QUESTION.match(item["question"])):
            problems.append(f"{where}: rule 4 (architecture) needs a pytanie file in 'question'")


def check(path: Path, data) -> list:
    if not isinstance(data, dict):
        return ["expected a JSON object"]
    problems = []
    missing, extra = KEYS - set(data), set(data) - KEYS - OPTIONAL
    if missing:
        problems.append(f"missing keys: {sorted(missing)}")
    if extra:
        problems.append(f"unknown keys: {sorted(extra)}")

    match = PLAN.match(str(data.get("plan")))
    if not match:
        problems.append("plan: expected loc/inbox/NNN-plan-<topic>.md or loc/inbox/done/...")
    elif match.group(2) != path.stem:
        problems.append(f"plan: number {match.group(2)} does not match the file name {path.name}")
    if data.get("mode") not in MODES:
        problems.append(f"mode: expected one of {sorted(MODES)}")
    if data.get("phase") not in PHASES:
        problems.append(f"phase: expected one of {sorted(PHASES)}")

    ids = check_milestones(data, problems)
    current = data.get("milestone")
    if not is_int(current) or not 1 <= current <= max(len(ids), 1):
        problems.append(f"milestone: expected 1..{len(ids)}")
    if data.get("phase") == "done":
        open_ = [m.get("id") for m in data.get("milestones") or []
                 if isinstance(m, dict) and m.get("status") not in ("done", "stuck")]
        if open_:
            problems.append(f"phase done but milestones still open: {open_}")

    # loc/state/NNN.json -> the project root is two levels up.
    project = path.resolve().parent.parent.parent
    check_gates(data, ids, project, problems)
    check_qa(data, project, problems)
    check_test_author(data, project, problems)
    check_deferred(data, project, problems)
    check_deviations(data, ids, problems)

    if not (isinstance(data.get("next_action"), str) and data["next_action"].strip()):
        problems.append("next_action: expected non-empty text")
    try:
        datetime.datetime.strptime(str(data.get("updated")), "%Y-%m-%d %H:%M")
    except ValueError:
        problems.append("updated: expected YYYY-MM-DD HH:MM")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("state", type=Path, help="state file, e.g. loc/state/018.json")
    args = parser.parse_args()
    try:
        # utf-8-sig: some editors on Windows add a BOM to a perfectly valid file.
        data = json.loads(args.state.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(json.dumps({"state": args.state.as_posix(), "ok": False, "error": str(error)}))
        return 2
    problems = check(args.state, data)
    print(json.dumps({"state": args.state.as_posix(), "ok": not problems, "problems": problems}, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
