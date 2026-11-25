#!/usr/bin/env python3
"""The log of a divergent milestone: the default answer, the variants, the critic's verdicts,
the pick and the build.

  --start --log <path> --default "<the answer most would give first>"
  --variant --log <path> --name <n> --move "<the means it uses>" --reason "<why, from a project fact>" [--safe]
      the same name again replaces the variant (a reworked one).
  --verdict --log <path> --name <n> --result pass|fail --why "<one sentence>"
  --pick --log <path> --name <n>|none --by user|interim
      `none` is the user's "None of them": new variants, then --start again.
  --built --log <path> --working pass|fail
      the picked variant is built in full and its working parts were checked.
  --check --log <path> [--moves loc/moves.md]
      prints `ok` when there are 2 to 4 variants, each with a reason, at most one safe one,
      at least 2 with the critic's pass, the picked one among them, the user picked it, it was
      built after that pick with its working parts passing, and its move is an entry of
      loc/moves.md; `waiting: user pick` when only the user's pick is missing; otherwise
      {"ok": false, "issues": [...]}. Not ok exits 1.

One line per event, its fields joined by ` | `; the last verdict and the last pick count, and a
reworked variant (the same name again) loses its earlier verdict.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SEP = " | "
ENTRY = re.compile(r"^- \S+ \(plan [^)]*\): (.+)$")


def clean(text: str) -> str:
    return " ".join(str(text).replace("|", "/").split())


def norm(text: str) -> str:
    return clean(text).lower()


def read(log: Path) -> dict:
    state = {"default": None, "variants": {}, "verdicts": {}, "pick": None, "built": None}
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.startswith("**Default:** "):
            state["default"] = line[len("**Default:** "):]
        if not line.startswith("- "):
            continue
        parts = line[2:].split(SEP)
        kind = parts[0]
        if kind == "variant" and len(parts) == 5:
            state["variants"][parts[1]] = {"move": parts[2], "reason": parts[3], "safe": parts[4] == "safe"}
            state["verdicts"].pop(parts[1], None)
        elif kind == "verdict" and len(parts) == 4:
            state["verdicts"][parts[1]] = parts[2]
        elif kind == "pick" and len(parts) == 3:
            state["pick"] = (parts[1], parts[2])
            if state["built"] and state["built"][0] != parts[1]:
                state["built"] = None
        elif kind == "built" and len(parts) == 3:
            state["built"] = (parts[1], parts[2])
    return state


def recorded(moves: Path) -> set:
    if not moves.is_file():
        return set()
    found = (ENTRY.match(line) for line in moves.read_text(encoding="utf-8").splitlines())
    return {norm(match.group(1)) for match in found if match}


def check(log: Path, moves: Path) -> tuple:
    if not log.is_file():
        return 1, {"ok": False, "issues": [f"no log at {log.as_posix()}: start it with --start"]}
    state, issues = read(log), []
    if not state["default"]:
        issues.append("no **Default:**: --start --default \"<the first answer>\"")
    variants = state["variants"]
    if not 2 <= len(variants) <= 4:
        issues.append(f"2 to 4 variants, found {len(variants)}")
    passed = [name for name in variants if state["verdicts"].get(name) == "pass"]
    if len(passed) < 2:
        issues.append(f"at least 2 variants with the critic's pass, found {len(passed)}: the milestone is stuck")
    for name, variant in variants.items():
        if not variant["reason"].strip("- "):
            issues.append(f"variant {name} has no reason")
    if sum(v["safe"] for v in variants.values()) > 1:
        issues.append("at most one safe variant")
    waiting = False
    if not state["pick"]:
        issues.append("no pick: --pick --name <n> --by user|interim")
    else:
        name, by = state["pick"]
        if name == "none":
            issues.append("the user picked none: new variants (a deferred file), then --start again")
        elif name not in variants:
            issues.append(f"the pick {name} is not a variant")
        elif state["verdicts"].get(name) != "pass":
            issues.append(f"{name} has no critic's pass")
        if name in variants and norm(variants[name]["move"]) not in recorded(moves):
            issues.append(f"the move of {name} is not in {moves.as_posix()}: moves.py add \"<move>\"")
        waiting = by != "user"
    built = state["built"]
    if state["pick"] and state["pick"][0] != "none":
        if not built or built[0] != state["pick"][0]:
            issues.append(f"{state['pick'][0]} is not built: --built --working pass after building it")
        elif built[1] != "pass":
            issues.append(f"the working parts of {built[0]} fail: fix them, then --built --working pass")
    if not issues and waiting:
        return 1, "waiting: user pick"
    if waiting:
        issues.append("waiting: user pick")
    return (1, {"ok": False, "issues": issues}) if issues else (0, "ok")


def append(log: Path, *fields: str) -> None:
    with log.open("a", encoding="utf-8") as out:
        out.write("- " + SEP.join(clean(field) or "-" for field in fields) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("start", "variant", "verdict", "pick", "built", "check"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--default")
    parser.add_argument("--name")
    parser.add_argument("--move")
    parser.add_argument("--reason")
    parser.add_argument("--safe", action="store_true")
    parser.add_argument("--result", choices=("pass", "fail"))
    parser.add_argument("--why")
    parser.add_argument("--by", choices=("user", "interim"))
    parser.add_argument("--working", choices=("pass", "fail"))
    parser.add_argument("--moves", type=Path, default=Path("loc/moves.md"))
    args = parser.parse_args()

    def fail(problem: str) -> int:
        print(json.dumps({"ok": False, "issues": [problem]}))
        return 1

    if args.check:
        code, result = check(args.log, args.moves)
        print(result if isinstance(result, str) else json.dumps(result))
        return code
    if args.start:
        if not (args.default or "").strip():
            return fail("--start needs --default \"<the answer most would give first>\"")
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(f"# Divergent log\n\n**Default:** {clean(args.default)}\n\n", encoding="utf-8")
    elif not args.log.is_file():
        return fail(f"no log at {args.log.as_posix()}: start it with --start")
    elif args.variant:
        if not (args.name and (args.move or "").strip() and (args.reason or "").strip()):
            return fail("--variant needs --name, --move and a reason (--reason, from a project fact)")
        append(args.log, "variant", args.name, args.move, args.reason, "safe" if args.safe else "-")
    elif args.verdict:
        if not (args.name and args.result and (args.why or "").strip()):
            return fail("--verdict needs --name, --result pass|fail and --why")
        append(args.log, "verdict", args.name, args.result, args.why)
    elif args.pick:
        if not (args.name and args.by):
            return fail("--pick needs --name and --by user|interim")
        append(args.log, "pick", args.name, args.by)
    elif args.built:
        pick = read(args.log)["pick"]
        if not (pick and args.working):
            return fail("--built needs a pick first and --working pass|fail (the working parts checked)")
        append(args.log, "built", pick[0], args.working)
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
