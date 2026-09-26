#!/usr/bin/env python3
"""Validate a plan execution state file, `tmp/state/<NNN>.json`.

`loc-orchestrate` writes the file after every step, so a new session (after
/clear or compaction) resumes from it without asking. Schema, all keys required:

    {
      "plan": "inbox/018-plan-csv-export.md",   # or inbox/done/..., NNN = file name
      "mode": "inline" | "subagent",
      "milestone": 1,                            # current one, 1-based
      "phase": "start" | "implement" | "proof" | "code-review"
               | "final-review" | "journal" | "done",
      "milestones": [
        {"id": "M1", "status": "pending" | "in_progress" | "done" | "stuck",
         "start": "<snapshot hash>" | null, "end": "<snapshot hash>" | null}
      ],
      "gates": {                                 # "M1/proof", "M1/code-review", "final-review"
        "M1/proof": {"rounds": 3, "passed": false, "stuck": "inbox/004-utknelo-....md"}
      },
      "deviations": [{"milestone": "M1", "rule": 1-4, "note": "...",
                      "question": "inbox/NNN-pytanie-....md"}],   # question: rule 4 only
      "next_action": "exactly what to do next",
      "updated": "YYYY-MM-DD HH:MM"
    }

Gate rules: at most 3 rounds; a gate that used 3 rounds without passing names its
`utknelo` file, and that file must exist in `inbox/` or `inbox/done/`.

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
MODES = {"inline", "subagent"}
PHASES = {"start", "implement", "proof", "code-review", "final-review", "journal", "done"}
STATUSES = {"pending", "in_progress", "done", "stuck"}
MAX_ROUNDS = 3
PLAN = re.compile(r"^inbox/(done/)?(\d{3,})-plan-[^/]+\.md$")
GATE = re.compile(r"^(M\d+)/(proof|code-review)$|^final-review$")
STUCK = re.compile(r"^inbox/(done/)?\d{3,}-utknelo-[^/]+\.md$")
QUESTION = re.compile(r"^inbox/(done/)?\d{3,}-pytanie-[^/]+\.md$")
HASH = re.compile(r"^[0-9a-f]{7,40}$")


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
            problems.append(f"gates: unknown gate {name!r} (M<n>/proof, M<n>/code-review, final-review)")
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
            elif not any((project / p).is_file() for p in (stuck, stuck.replace("inbox/", "inbox/done/", 1))):
                problems.append(f"gates.{name}.stuck: {stuck} does not exist")
        elif stuck is not None:
            problems.append(f"gates.{name}.stuck: only a gate that failed {MAX_ROUNDS} rounds has one")


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
    missing, extra = KEYS - set(data), set(data) - KEYS
    if missing:
        problems.append(f"missing keys: {sorted(missing)}")
    if extra:
        problems.append(f"unknown keys: {sorted(extra)}")

    match = PLAN.match(str(data.get("plan")))
    if not match:
        problems.append("plan: expected inbox/NNN-plan-<topic>.md or inbox/done/...")
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

    # tmp/state/NNN.json -> the project root is two levels up.
    check_gates(data, ids, path.resolve().parent.parent.parent, problems)
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
    parser.add_argument("state", type=Path, help="state file, e.g. tmp/state/018.json")
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
