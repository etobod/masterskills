#!/usr/bin/env python3
"""Enforce the plugin's word budget (spec section 9).

Counts whitespace-separated words in every always-loaded or on-demand text
file of the plugin and compares them with their limit:

    rules/*.md                    470 words in total (one always-loaded block)
    skills/*/SKILL.md             800 words per skill core
    skills/*/references/*.md      800 words per reference
    agents/*.md                   600 words per agent definition
    opencode/agents/*.md          600 words per OpenCode-only agent

Exceptions approved by the user are listed in OVERRIDES.

Prints a JSON report to stdout. Exit code: 0 all within budget, 1 at least
one item over budget, 2 bad arguments.
"""

import argparse
import json
import sys
from pathlib import Path

LIMITS = {
    "rule": 470,
    "skill": 800,
    "reference": 800,
    "agent": 600,
}

# Per-file limits approved by the user; everything else uses LIMITS.
OVERRIDES = {
    "skills/loc-orchestrate/SKILL.md": 1350,
    "skills/loc-planning/SKILL.md": 2720,
    "skills/loc-review/SKILL.md": 900,
    "skills/loc-diagram/SKILL.md": 850,
    "skills/loc-qa/SKILL.md": 1000,
    "agents/rubber-duck.md": 650,
    "agents/judge.md": 650,
}

PATTERNS = [
    ("rule", "rules/*.md"),
    ("skill", "skills/*/SKILL.md"),
    ("reference", "skills/*/references/*.md"),
    ("agent", "agents/*.md"),
    ("agent", "opencode/agents/*.md"),
]


def count_words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def measure(root: Path) -> dict:
    items = []
    for kind, pattern in PATTERNS:
        for path in sorted(root.glob(pattern)):
            words = count_words(path)
            items.append({
                "kind": kind,
                "path": path.relative_to(root).as_posix(),
                "words": words,
            })

    for item in items:
        if item["kind"] != "rule":
            item["limit"] = OVERRIDES.get(item["path"], LIMITS[item["kind"]])
            item["ok"] = item["words"] <= item["limit"]

    # Rules are injected together, so the budget applies to their sum.
    rule_items = [i for i in items if i["kind"] == "rule"]
    rules_total = sum(i["words"] for i in rule_items)
    rules = {
        "files": len(rule_items),
        "words": rules_total,
        "limit": LIMITS["rule"],
        "ok": rules_total <= LIMITS["rule"],
    }

    over = [i["path"] for i in items if i["kind"] != "rule" and not i["ok"]]
    if not rules["ok"]:
        over.append("rules/*.md (total)")

    return {
        "root": root.as_posix(),
        "ok": not over,
        "rules": rules,
        "items": items,
        "over": over,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="plugin root to measure (default: this repository)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"root is not a directory: {root.as_posix()}"}))
        return 2

    report = measure(root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
