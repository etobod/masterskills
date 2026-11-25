#!/usr/bin/env python3
"""A random start for a divergent milestone, so its variants do not all begin at the first idea.

  seed.py visual|text|idea [--keep <axis>=<value>]... [--only <axis>]... [--history loc/seeds.jsonl]

Draws one value per axis with `random.SystemRandom`. The axes belong to no project: they
name means (a method, a register, a constraint), never content. `--keep` fixes an axis,
`--only` draws only the axes named. A value used by one of the last 12 seeds of the same
kind is skipped while the axis has others. Every seed is appended to the history file
(in the project, never the home directory). Prints {"kind", "seed"}.
"""

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

RECENT = 12

VERB = ["fold", "cut", "stack", "repeat", "invert", "enlarge", "shrink", "omit", "borrow",
        "translate", "slow down", "count", "label", "mirror", "interrupt"]
SCALE = ["everything tiny", "one element huge", "life size", "a single detail up close",
         "seen from far away", "map scale", "pocket size", "poster size", "one word per screen",
         "a hundred items at once", "room size", "one line only", "a whole year at once", "a second"]

AXES = {
    "visual": {
        "method": ["collage of cut shapes", "a single continuous line", "a grid broken in one place",
                   "a hard-cropped photograph", "type as the image", "hand-drawn marks",
                   "a diagram used as ornament", "one oversized element", "a repeated small unit",
                   "layered translucent planes", "a two-ink print", "a texture from a real material",
                   "negative space carries the shape", "stamp and ink", "a technical drawing"],
        "colours": ["two inks only", "black, white and one signal colour",
                    "the colours of one material (paper, rust, concrete)", "pale tints against dark text",
                    "a single hue in five steps", "a muted complementary pair", "earth tones and one neon",
                    "newsprint grey and red", "a night palette", "faded print colours", "chalkboard colours",
                    "warning colours used calmly", "all blues", "the colours of one food",
                    "neutrals only, colour only in images"],
        "layout": ["one column with wide margins", "an asymmetric split", "a strict baseline grid",
                   "a list instead of cards", "content in the margins", "one screen, nothing scrolls",
                   "an index down one side", "stacked full-width bands", "centred and narrow", "a dense table",
                   "overlapping layers", "weight at the bottom", "an image edge to edge with text over it",
                   "a timeline"],
        "typography": ["one serif in many sizes", "monospace everywhere",
                       "condensed sans headings over a book serif", "all lowercase", "huge numerals",
                       "a single weight", "a slab serif", "handwritten accents", "small-caps labels",
                       "wide-tracked labels", "type set vertically", "a display face used once",
                       "a rounded sans", "a tight grotesque"],
        "verb": VERB,
        "scale": SCALE,
    },
    "text": {
        "voice": ["a field guide", "a ship's log", "a shop sign", "a recipe", "a weather report",
                  "a museum label", "a letter to a friend", "an old appliance manual", "a sports commentator",
                  "a lab notebook", "a dictionary entry", "a radio announcer", "a postcard", "a timetable"],
        "entry": ["a number", "a verb", "the problem", "an object", "a place", "mid-sentence",
                  "the user's own question", "what it does not do", "a time of day", "a sound", "a list",
                  "a comparison", "a name", "a mistake"],
        "register": ["plain and dry", "warm and short", "formal", "playful but exact", "technical", "spoken",
                     "terse as a label", "old-fashioned", "deadpan", "calm and slow", "urgent",
                     "quiet and precise", "conversational", "ceremonial"],
    },
    "idea": {
        "verb": VERB,
        "constraint": ["works offline", "one screen only", "no text", "one input", "no account", "one colour",
                       "fits in one sentence", "one minute to use", "no settings", "built from existing parts",
                       "no mouse", "readable on paper", "no numbers shown", "one action a day"],
        "scale": SCALE,
        "emphasis": ["speed", "trust", "play", "memory", "craft", "silence", "habit", "surprise", "precision",
                     "company", "privacy", "patience", "clarity", "ownership"],
    },
}


def recent(history: Path, kind: str) -> list:
    if not history.is_file():
        return []
    seeds = []
    for line in history.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("kind") == kind and isinstance(entry.get("seed"), dict):
            seeds.append(entry["seed"])
    return seeds[-RECENT:]


def draw(kind: str, keep: dict, only: list, history: Path, rng=None) -> dict:
    rng = rng or random.SystemRandom()
    axes = AXES[kind]
    used = recent(history, kind)
    seed = {}
    for axis, values in axes.items():
        if axis in keep:
            seed[axis] = keep[axis]
            continue
        if only and axis not in only:
            continue
        fresh = [v for v in values if all(s.get(axis) != v for s in used)]
        seed[axis] = rng.choice(fresh or values)
    return seed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("kind", choices=sorted(AXES))
    parser.add_argument("--keep", action="append", default=[], metavar="AXIS=VALUE")
    parser.add_argument("--only", action="append", default=[], metavar="AXIS")
    parser.add_argument("--history", type=Path, default=Path("loc/seeds.jsonl"))
    args = parser.parse_args()
    axes = AXES[args.kind]
    keep, problems = {}, []
    for item in args.keep:
        axis, _, value = item.partition("=")
        if axis not in axes or not value.strip():
            problems.append(f"--keep {item!r}: an axis of {args.kind} ({', '.join(axes)}) and a value")
        keep[axis] = value.strip()
    for axis in args.only:
        if axis not in axes:
            problems.append(f"--only {axis!r}: not an axis of {args.kind} ({', '.join(axes)})")
    if problems:
        print(json.dumps({"ok": False, "issues": problems}))
        return 1
    seed = draw(args.kind, keep, args.only, args.history)
    args.history.parent.mkdir(parents=True, exist_ok=True)
    with args.history.open("a", encoding="utf-8") as out:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        out.write(json.dumps({"kind": args.kind, "at": stamp, "seed": seed}) + "\n")
    print(json.dumps({"kind": args.kind, "seed": seed}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
