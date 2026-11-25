#!/usr/bin/env python3
"""Sum the tokens a plan run cost, from the Claude Code session logs of the project.

Reads `<config>/projects/<project dir>/*.jsonl` (main sessions) and
`*/subagents/*.jsonl` (agents, typed by the `.meta.json` beside them), where
<config> is `CLAUDE_CONFIG_DIR` or `~/.claude` and <project dir> is the
project's path with every character other than a letter or digit turned into
`-`. Counts each API response once (input, cache writes, cache reads, output)
whose timestamp lies in the plan's window: from the commit time of
`milestones[0].start` in the state file (or `--since`) to now (or `--until`).

    plan_cost.py --state loc/state/<NNN>.json [--since <iso>] [--until <iso>] [--logs <dir>]

Prints one line, e.g. `1.8M tokens: main 35%, rubber-duck 40%, qa 10%`, or
`cost unknown` when there are no logs (another tool ran the plan). `--json`
prints {"total", "by"} instead. Exit 0, or 2 when the state file cannot be read.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import git  # noqa: E402


def logs_dir(project: Path) -> Path:
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return config / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project))


def moment(text: str) -> datetime:
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def agent_type(log: Path) -> str:
    try:
        meta = json.loads(log.with_name(log.name[:-len(".jsonl")] + ".meta.json").read_text(encoding="utf-8"))
        name = meta.get("agentType") or "agent"
    except (OSError, ValueError):
        name = "agent"
    return name.split(":")[-1]


def usage_of(log: Path, since: datetime, until: datetime) -> int:
    """Tokens of each response in the window; a response logged in several lines counts once."""
    seen = {}
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message") if isinstance(entry, dict) else None
        usage = message.get("usage") if isinstance(message, dict) else None
        if not isinstance(usage, dict) or not entry.get("timestamp"):
            continue
        try:
            when = moment(entry["timestamp"])
        except ValueError:
            continue
        if not since <= when <= until:
            continue
        key = message.get("id") or entry.get("requestId") or entry.get("uuid")
        seen[key] = sum(usage.get(part) or 0 for part in
                        ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    return sum(seen.values())


def cost(logs: Path, since: datetime, until: datetime) -> dict:
    by = {}
    for log in sorted(logs.glob("*.jsonl")):
        by["main"] = by.get("main", 0) + usage_of(log, since, until)
    for log in sorted(logs.glob("*/subagents/*.jsonl")):
        name = agent_type(log)
        by[name] = by.get(name, 0) + usage_of(log, since, until)
    by = {name: tokens for name, tokens in by.items() if tokens}
    return {"total": sum(by.values()), "by": dict(sorted(by.items(), key=lambda item: -item[1]))}


def short(tokens: int) -> str:
    for size, unit in ((1_000_000, "M"), (1_000, "k")):
        if tokens >= size:
            return f"{tokens / size:.1f}".rstrip("0").rstrip(".") + unit
    return str(tokens)


def line(result: dict) -> str:
    if not result["total"]:
        return "cost unknown"
    parts = [f"{name} {round(100 * tokens / result['total'])}%" for name, tokens in result["by"].items()]
    return f"{short(result['total'])} tokens: " + ", ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path,
                        default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    parser.add_argument("--state", type=Path, required=True, help="loc/state/<NNN>.json")
    parser.add_argument("--since", help="start of the window, ISO time (default: the plan's first snapshot)")
    parser.add_argument("--until", help="end of the window, ISO time (default: now)")
    parser.add_argument("--logs", type=Path, help="session log directory (default: the project's)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve()
    state = args.state if args.state.is_absolute() else project / args.state
    try:
        if args.since:
            since = moment(args.since)
        else:
            data = json.loads(state.read_text(encoding="utf-8"))
            start = (data.get("milestones") or [{}])[0].get("start")
            if not start:
                raise ValueError("milestones[0].start: no first snapshot in the state file")
            since = moment(git(["show", "-s", "--format=%cI", start], project))
        until = moment(args.until) if args.until else datetime.now(timezone.utc)
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    logs = args.logs or logs_dir(project)
    result = cost(logs, since, until) if logs.is_dir() else {"total": 0, "by": {}}
    print(json.dumps(result, indent=2) if args.json else line(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
