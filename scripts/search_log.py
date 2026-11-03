#!/usr/bin/env python3
"""The log of a search milestone: every try, what is kept, and when the search stops.

The orchestrator measures; this script decides, so a model never judges its own score.

  --start --log <path> --metric "<command>" [--quick "<command>"] --baseline <x> --target ">= 80"
          --budget <n> --give-up <n>
      creates the log; prints {"best", "stop"} (stop "target" when the baseline already meets it).
      With --quick, the baseline and every try are quick scores, and a quick score never ends the
      search by itself: the full metric confirms it.
  --add --log <path> --score <x> --hypothesis "<idea>" --change "<what changed>"
      records a try; prints {"iteration", "keep", "best", "stop", "confirm"}. `keep` only when the
      score beats the best so far in the target's direction; `stop` is "target", "budget",
      "give-up" or null; `confirm` is true when a kept quick score meets the target.
  --confirm --log <path> --full <x>
      records the full metric of the kept change; meeting the target stops the search ("target"),
      otherwise it goes on. Not a try: it uses no iteration. Prints {"stop"}.
  --metric-change --log <path> --reason "<why>" --baseline <x> --best <x>
      records a metric change the judge approved, with the baseline and best measured again;
      at most 2 per search, a third prints {"ok": false, "question": true} and exits 1.
  --stop --log <path> --reason "<why>"
      the searcher gave up early.
  --check --log <path>
      prints `ok` when the log is complete (baseline, tries numbered within the budget, a stop
      reason), else {"ok": false, "issues": [...]} and exits 1.

Scores may carry a `%`. A try's text has `|` replaced, so the table stays readable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

MAX_METRIC_CHANGES = 2
TARGET = re.compile(r"^\s*(>=|<=|≥|≤)\s*(-?\d+(?:\.\d+)?)\s*%?\s*$")
FIELD = re.compile(r"^\*\*(?P<key>[A-Za-z ]+):\*\*\s*(?P<value>.*?)\s*$")
ROW = re.compile(r"^\|\s*(?P<n>[^|]*?)\s*\|\s*(?P<score>[^|]*?)\s*\|\s*(?P<kept>[^|]*?)\s*\|"
                 r"\s*(?P<hypothesis>[^|]*?)\s*\|\s*(?P<change>[^|]*?)\s*\|$")
HEADER = "| # | Score | Kept | Hypothesis | Change |\n|---|---|---|---|---|\n"


def number(text: str) -> float:
    return float(str(text).strip().rstrip("%").strip())


def clean(text: str) -> str:
    return " ".join(str(text).replace("|", "/").split()) or "-"


def target(text: str):
    match = TARGET.match(text)
    if not match:
        return None
    higher = match.group(1) in (">=", "≥")
    return higher, float(match.group(2))


def read(path: Path) -> dict:
    log = {"fields": {}, "rows": [], "stopped": None}
    for line in path.read_text(encoding="utf-8").splitlines():
        field = FIELD.match(line)
        if field:
            if field.group("key") == "Stopped":
                log["stopped"] = field.group("value")
            else:
                log["fields"][field.group("key")] = field.group("value")
            continue
        row = ROW.match(line)
        if row and row.group("n") not in ("#", "---"):
            log["rows"].append(row.groupdict())
    return log


def state(log: dict) -> dict:
    """Best score, tries since the last metric change, tries without a gain, metric changes."""
    higher, _ = target(log["fields"]["Target"])
    best, tries, streak, changes = None, 0, 0, 0
    for row in log["rows"]:
        if row["kept"].startswith("full"):
            continue
        if row["kept"] in ("baseline", "metric change"):
            best, streak = number(row["score"]), 0
            changes += row["kept"] == "metric change"
            continue
        tries += 1
        if row["kept"] == "kept":
            best, streak = number(row["score"]), 0
        else:
            streak += 1
    return {"best": best, "tries": tries, "streak": streak, "changes": changes, "higher": higher}


def reached(value: float, higher: bool, goal: float) -> bool:
    return value >= goal if higher else value <= goal


def append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def fail(message: str, **extra) -> int:
    print(json.dumps({"ok": False, "error": message, **extra}))
    return 1


def start(args) -> int:
    path = Path(args.log)
    if path.exists():
        return fail(f"{path} exists; a resumed search continues with --add")
    if target(args.target) is None:
        return fail("target reads '>= <number>' or '<= <number>'")
    if args.budget < 1 or args.give_up < 1:
        return fail("budget and give-up are at least 1")
    path.parent.mkdir(parents=True, exist_ok=True)
    baseline = number(args.baseline)
    quick = f"**Quick metric:** `{args.quick}`\n" if args.quick else ""
    path.write_text(
        f"# Search log\n\n**Metric:** `{args.metric}`\n{quick}**Target:** {args.target}\n**Budget:** {args.budget}\n"
        f"**Give up:** {args.give_up}\n\n{HEADER}| 0 | {baseline:g} | baseline | - | - |\n",
        encoding="utf-8", newline="\n")
    higher, goal = target(args.target)
    stop = "target" if reached(baseline, higher, goal) and not args.quick else None
    if stop:
        append(path, "\n**Stopped:** target\n")
    print(json.dumps({"best": baseline, "stop": stop,
                      "confirm": bool(args.quick) and reached(baseline, higher, goal)}))
    return 0


def add(args) -> int:
    path = Path(args.log)
    log = read(path)
    if log["stopped"]:
        return fail(f"the search stopped: {log['stopped']}")
    now = state(log)
    score = number(args.score)
    higher, goal = target(log["fields"]["Target"])
    keep = score > now["best"] if higher else score < now["best"]
    iteration = now["tries"] + 1
    append(path, f"| {iteration} | {score:g} | {'kept' if keep else 'reverted'} | {clean(args.hypothesis)} | "
                 f"{clean(args.change)} |\n")
    best = score if keep else now["best"]
    streak = 0 if keep else now["streak"] + 1
    stop, quick = None, "Quick metric" in log["fields"]
    confirm = keep and quick and reached(best, higher, goal)
    if keep and not quick and reached(best, higher, goal):
        stop = "target"
    elif iteration >= int(log["fields"]["Budget"]):
        stop = "budget"
    elif streak >= int(log["fields"]["Give up"]):
        stop = "give-up"
    if stop:
        append(path, f"\n**Stopped:** {stop}\n")
    print(json.dumps({"iteration": iteration, "keep": keep, "best": best, "stop": stop, "confirm": confirm}))
    return 0


def confirm(args) -> int:
    path = Path(args.log)
    log = read(path)
    if log["stopped"]:
        return fail(f"the search stopped: {log['stopped']}")
    if "Quick metric" not in log["fields"]:
        return fail("no quick metric: the score of every try is already the full one")
    full = number(args.full)
    higher, goal = target(log["fields"]["Target"])
    met = reached(full, higher, goal)
    append(path, f"| c | {full:g} | {'full: target met' if met else 'full: below target'} | full metric | - |\n")
    stop = "target" if met else None
    if stop:
        append(path, "\n**Stopped:** target\n")
    print(json.dumps({"stop": stop}))
    return 0


def metric_change(args) -> int:
    path = Path(args.log)
    log = read(path)
    if log["stopped"]:
        return fail(f"the search stopped: {log['stopped']}")
    if state(log)["changes"] >= MAX_METRIC_CHANGES:
        return fail(f"at most {MAX_METRIC_CHANGES} metric changes per search; ask the user", question=True)
    append(path, f"| m | {number(args.best):g} | metric change | {clean(args.reason)} | "
                 f"baseline {number(args.baseline):g} |\n")
    print(json.dumps({"ok": True, "best": number(args.best)}))
    return 0


def stop(args) -> int:
    path = Path(args.log)
    log = read(path)
    if log["stopped"]:
        return fail(f"the search stopped: {log['stopped']}")
    append(path, f"\n**Stopped:** gave up: {clean(args.reason)}\n")
    print(json.dumps({"ok": True, "stop": "gave up"}))
    return 0


def check(args) -> int:
    path = Path(args.log)
    if not path.is_file():
        return fail(f"no log at {path}")
    log = read(path)
    issues = []
    for key in ("Metric", "Target", "Budget", "Give up"):
        if key not in log["fields"]:
            issues.append(f"missing **{key}:**")
    if "Target" in log["fields"] and target(log["fields"]["Target"]) is None:
        issues.append("**Target:** reads '>= <number>' or '<= <number>'")
    if not log["rows"] or log["rows"][0]["kept"] != "baseline":
        issues.append("the first row is the baseline")
    expected = 1
    for row in log["rows"][1:]:
        if row["kept"] == "metric change" or row["kept"].startswith("full"):
            continue
        if row["kept"] not in ("kept", "reverted"):
            issues.append(f"row {row['n']}: kept is 'kept' or 'reverted'")
        if row["n"] != str(expected):
            issues.append(f"row {row['n']}: expected try {expected}")
        expected += 1
    budget = log["fields"].get("Budget", "")
    if budget.isdigit() and expected - 1 > int(budget):
        issues.append(f"{expected - 1} tries over the budget of {budget}")
    if not log["stopped"]:
        issues.append("no **Stopped:** line (target, budget, give-up or gave up: <reason>)")
    if issues:
        print(json.dumps({"ok": False, "issues": issues}))
        return 1
    print("ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("start", "add", "confirm", "metric-change", "stop", "check"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--log", required=True)
    parser.add_argument("--metric")
    parser.add_argument("--quick")
    parser.add_argument("--full")
    parser.add_argument("--baseline")
    parser.add_argument("--target")
    parser.add_argument("--budget", type=int)
    parser.add_argument("--give-up", type=int)
    parser.add_argument("--score")
    parser.add_argument("--hypothesis", default="-")
    parser.add_argument("--change", default="-")
    parser.add_argument("--best")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    needed = {"start": ("metric", "baseline", "target", "budget", "give_up"), "add": ("score",), "confirm": ("full",),
              "metric_change": ("reason", "baseline", "best"), "stop": ("reason",), "check": ()}
    name = next(key for key in needed if getattr(args, key))
    missing = [key for key in needed[name] if getattr(args, key) in (None, "")]
    if missing:
        return fail("missing " + ", ".join("--" + key.replace("_", "-") for key in missing))
    if name != "start" and name != "check" and not Path(args.log).is_file():
        return fail(f"no log at {args.log}; start it with --start")
    try:
        return {"start": start, "add": add, "confirm": confirm, "metric_change": metric_change, "stop": stop, "check": check}[name](args)
    except ValueError as error:
        return fail(f"not a number: {error}")


if __name__ == "__main__":
    sys.exit(main())
