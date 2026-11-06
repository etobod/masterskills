#!/usr/bin/env python3
"""Keep the user's manual checks in one HTML sheet: `loc/inbox/NNN-U-checks.html`.

Every edit of the sheet goes through this script; the model never edits it by hand.

- `--add` appends a numbered point to the open sheet, or starts a new sheet with the
  next inbox number when none is open. A point holds its plan and milestone, the steps
  (an image per step with a "click here" ring at `x,y` percent), what to look at, what
  was expected and what was seen, screenshots and references. Images are copied to
  `loc/tmp/checks/`, so the sheet never points at files that may change.
- `--ok N ...` and `--fix N "<what>"` move rated points, with the answer and the date,
  into the same-named file in `loc/inbox/done/` and delete their images there (a caption
  stays). When the last point leaves, the open sheet is deleted; the next `--add`
  starts a new sheet with a new number.
- `--list` prints the open points.

Point numbers count up within a sheet and are never reused, so "3 ok" means one thing.
Each point sits between `<!-- point N -->` and `<!-- /point N -->`, so moving one never
touches the others.

Prints JSON, e.g. {"sheet": "loc/inbox/024-U-checks.html", "point": 3, "open": 3}
or {"sheet": ..., "moved": [3, 5], "fixes": [{"point", "plan", "milestone", "title", "fix"}],
"open": 1, "closed": false}.
"""

import argparse
import datetime
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from next_number import next_number  # noqa: E402

SHEET = re.compile(r"^(\d{3,})-U-checks\.html$")
POINT = re.compile(r"<!-- point (\d+) -->\n(.*?)<!-- /point \1 -->\n", re.S)
HEAD = re.compile(r"<!-- head -->.*?<!-- /head -->", re.S)
FIGURE = re.compile(r'<figure class="(?:shot|step)"><span class="frame"><img src="([^"]*)" alt="[^"]*">(.*?)</span>(?:<figcaption>(.*?)</figcaption>)?</figure>', re.S)
ATTR = re.compile(r'data-(plan|milestone|title|blocking)="([^"]*)"')
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

STYLE = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--muted:#5b6475;--line:#d9dde5;--accent:#2457d6;--warn:#b3261e;--ok:#1e7a46}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--card:#1b2029;--ink:#e6e9ef;--muted:#9aa3b5;--line:#2d3442;--accent:#7ea2ff;--warn:#ff8a80;--ok:#6fd39b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}
header{padding:16px 0 8px;border-bottom:1px solid var(--line);margin-bottom:16px}
h1{font-size:1.4rem;margin:0 0 4px}.how{color:var(--muted);margin:4px 0}code{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:1px 5px}
.check{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
.check[data-blocking="true"]{border:2px solid var(--warn)}
.top{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
.num{font-size:2.4rem;font-weight:700;line-height:1;color:var(--accent)}
.check h2{font-size:1.15rem;margin:0}.where{color:var(--muted);font-size:.9rem}
.badge{color:var(--warn);font-weight:600;font-size:.9rem}
.check h3{font-size:.95rem;margin:14px 0 4px}
.check ol,.check ul{margin:4px 0;padding-left:22px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:640px){.pair{grid-template-columns:1fr}}
.pair div{border-left:3px solid var(--line);padding-left:10px}
.shots{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}
figure{margin:6px 0;max-width:100%}figure.step{margin:8px 0 12px;max-width:640px}
.frame{position:relative;display:inline-block;max-width:100%;vertical-align:top}
.frame img{display:block;max-width:100%;max-height:70vh;border:1px solid var(--line);border-radius:6px}
.shots figure{flex:0 1 340px;min-width:0}.shots .frame img{width:100%}
figcaption{color:var(--muted);font-size:.85rem}
.tap{position:absolute;width:34px;height:34px;border:4px solid #e0245e;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 3px #fff8;pointer-events:none}
.answer{font-weight:600}.answer.ok{color:var(--ok)}.answer.fix{color:var(--warn)}.gone{color:var(--muted);font-style:italic}
"""


def find_sheet(project: Path):
    inbox = project / "loc" / "inbox"
    found = sorted(p for p in inbox.glob("*-U-checks.html") if SHEET.match(p.name)) if inbox.is_dir() else []
    return found[-1] if found else None


def head(number: str, open_points: int, done: bool) -> str:
    if done:
        how = "Rated points, with the user's answers."
    else:
        how = ("Answer in the chat with the numbers, e.g. <code>3 ok, 5 fix: the shadow is too strong</code>. "
               "A point with a red frame stops the work until you answer it.")
    return (f"<!-- head --><header><h1>{number} — Manual checks</h1>"
            f"<p class=\"how\"><b>{open_points}</b> {'rated' if done else 'open'}. {how}</p></header><!-- /head -->")


def page(number: str, done: bool) -> str:
    title = f"{number} — Manual checks" + (" (rated)" if done else "")
    return (f"<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{title}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n<main>\n"
            f"{head(number, 0, done)}\n<!-- points -->\n</main>\n</body>\n</html>\n")


def points(text: str) -> list:
    return [(int(m.group(1)), m.group(0)) for m in POINT.finditer(text)]


def refresh(text: str, number: str, done: bool) -> str:
    return HEAD.sub(lambda _: head(number, len(points(text)), done), text, count=1)


def split(value: str) -> list:
    return [part.strip() for part in value.split("|")]


def copy_image(project: Path, source: str, number: str, point: int, index: int) -> str:
    path = Path(source)
    if not path.is_absolute():
        path = project / path if (project / path).is_file() else Path.cwd() / path
    if not path.is_file():
        raise SystemExit(json.dumps({"error": f"image not found: {source}"}))
    if path.suffix.lower() not in IMAGE_TYPES:
        raise SystemExit(json.dumps({"error": f"not an image: {source}"}))
    target = project / "loc" / "tmp" / "checks" / f"{number}-{point}-{index}{path.suffix.lower()}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    return f"../tmp/checks/{target.name}"


def figure(src: str, caption: str, tap: str = "", kind: str = "shot") -> str:
    ring = ""
    if tap:
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*", tap)
        if not match:
            raise SystemExit(json.dumps({"error": f"click position is x,y in percent: {tap}"}))
        ring = f'<span class="tap" style="left:{match[1]}%;top:{match[2]}%"></span>'
    cap = html.escape(caption)
    caption_html = "" if kind == "step" else f"<figcaption>{cap}</figcaption>"
    return f'<figure class="{kind}"><span class="frame"><img src="{html.escape(src)}" alt="{cap}">{ring}</span>{caption_html}</figure>'


def build_point(project: Path, number: str, point: int, args) -> str:
    esc = html.escape
    images = iter(range(1, 1000))
    parts = [f'<section class="check" id="p{point}" data-point="{point}" data-plan="{esc(args.plan or "")}" '
             f'data-milestone="{esc(args.milestone or "")}" data-title="{esc(args.title)}"'
             + (' data-blocking="true"' if args.blocking else "") + ">"]
    where = " · ".join(x for x in (f"plan {args.plan}" if args.plan else "", args.milestone or "") if x)
    badges = []
    if args.again:
        badges.append(f'<span class="where">again: {args.again}</span>')
    if args.blocking:
        badges.append('<span class="badge">blocking: the work waits for this answer</span>')
    parts.append(f'<div class="top"><span class="num">{point}</span><h2>{esc(args.title)}</h2>'
                 f'<span class="where">{esc(where)}</span>{"".join(badges)}</div>')
    if args.step:
        items = []
        for step in args.step:
            text, image, tap = (split(step) + ["", ""])[:3]
            body = esc(text)
            if image:
                body += figure(copy_image(project, image, number, point, next(images)), text, tap, "step")
            items.append(f"<li>{body}</li>")
        parts.append(f"<h3>Steps</h3><ol>{''.join(items)}</ol>")
    parts.append("<h3>Look at</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in args.look) + "</ul>")
    if args.expected or args.seen:
        parts.append('<div class="pair">'
                     + (f"<div><h3>Expected</h3><p>{esc(args.expected)}</p></div>" if args.expected else "")
                     + (f"<div><h3>Seen by the critic</h3><p>{esc(args.seen)}</p></div>" if args.seen else "")
                     + "</div>")
    for heading, values in (("Screenshots", args.image), ("References", args.reference)):
        if values:
            figs = []
            for value in values:
                image, caption = (split(value) + [""])[:2]
                figs.append(figure(copy_image(project, image, number, point, next(images)), caption or Path(image).name))
            parts.append(f'<h3>{heading}</h3><div class="shots">{"".join(figs)}</div>')
    parts.append("</section>")
    return f"<!-- point {point} -->\n" + "\n".join(parts) + f"\n<!-- /point {point} -->\n"


def add(project: Path, args) -> dict:
    sheet = find_sheet(project)
    if sheet is None:
        number = next_number(project)
        sheet = project / "loc" / "inbox" / f"{number}-U-checks.html"
        sheet.parent.mkdir(parents=True, exist_ok=True)
        text = page(number, done=False)
    else:
        number = SHEET.match(sheet.name).group(1)
        text = sheet.read_text(encoding="utf-8")
    done = project / "loc" / "inbox" / "done" / sheet.name
    used = [n for n, _ in points(text)]
    if done.is_file():
        used += [n for n, _ in points(done.read_text(encoding="utf-8"))]
    point = max(used, default=0) + 1
    block = build_point(project, number, point, args)
    text = text.replace("</main>", block + "</main>", 1)
    text = refresh(text, number, done=False)
    sheet.write_text(text, encoding="utf-8", newline="\n")
    return {"sheet": sheet.relative_to(project).as_posix(), "point": point, "open": len(points(text))}


def add_point(project: Path, title: str, look: list, **fields) -> dict:
    """Append a point from Python (the migration); fields are the `--add` options."""
    values = {"plan": None, "milestone": None, "step": [], "image": [], "reference": [], "expected": None,
              "seen": None, "again": None, "blocking": False, **fields}
    return add(project, argparse.Namespace(title=title, look=look, **values))


def rate(project: Path, ok: list, fixes: list) -> dict:
    sheet = find_sheet(project)
    if sheet is None:
        raise SystemExit(json.dumps({"error": "no open checks sheet"}))
    number = SHEET.match(sheet.name).group(1)
    text = sheet.read_text(encoding="utf-8")
    blocks = dict(points(text))
    answers = {n: ("ok", "") for n in ok}
    answers.update({int(n): ("fix", what) for n, what in fixes})
    missing = sorted(n for n in answers if n not in blocks)
    if missing:
        raise SystemExit(json.dumps({"error": f"no open point {', '.join(map(str, missing))} in {sheet.name}"}))
    done = project / "loc" / "inbox" / "done" / sheet.name
    done.parent.mkdir(parents=True, exist_ok=True)
    rated = done.read_text(encoding="utf-8") if done.is_file() else page(number, done=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    result = {"sheet": sheet.relative_to(project).as_posix(), "moved": [], "fixes": []}
    for n in sorted(answers):
        block = blocks[n]
        verdict, what = answers[n]
        attrs = dict(ATTR.findall(block))
        for src, _, _ in FIGURE.findall(block):
            image = (sheet.parent / src).resolve()
            if image.is_file() and (project / "loc" / "tmp" / "checks") in image.parents:
                image.unlink()
        moved = FIGURE.sub(lambda m: f'<p class="gone">screenshot removed after rating: {m.group(3) or "step image"}</p>', block)
        line = f"Rated {stamp}: ok" if verdict == "ok" else f"Rated {stamp}: fix: {html.escape(what)}"
        moved = moved.replace("</section>", f'<p class="answer {verdict}">{line}</p>\n</section>', 1)
        rated = rated.replace("</main>", moved + "</main>", 1)
        text = text.replace(block, "", 1)
        result["moved"].append(n)
        if verdict == "fix":
            result["fixes"].append({"point": n, "plan": attrs.get("plan", ""), "milestone": attrs.get("milestone", ""),
                                    "title": html.unescape(attrs.get("title", "")), "fix": what})
    done.write_text(refresh(rated, number, done=True), encoding="utf-8", newline="\n")
    left = len(points(text))
    if left:
        sheet.write_text(refresh(text, number, done=False), encoding="utf-8", newline="\n")
    else:
        sheet.unlink()
    result.update(open=left, closed=not left, done=done.relative_to(project).as_posix())
    return result


def listing(project: Path) -> dict:
    sheet = find_sheet(project)
    if sheet is None:
        return {"sheet": None, "points": []}
    found = []
    for n, block in points(sheet.read_text(encoding="utf-8")):
        attrs = dict(ATTR.findall(block))
        found.append({"point": n, "plan": attrs.get("plan", ""), "milestone": attrs.get("milestone", ""),
                      "title": html.unescape(attrs.get("title", "")), "blocking": attrs.get("blocking") == "true"})
    return {"sheet": sheet.relative_to(project).as_posix(), "points": found}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()),
                        help="project root (default: $CLAUDE_PROJECT_DIR, then the current directory)")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--add", action="store_true", help="append a point")
    action.add_argument("--list", action="store_true", help="print the open points")
    action.add_argument("--rate", action="store_true", help="move rated points to loc/inbox/done/ (with --ok/--fix)")
    parser.add_argument("--plan", help="plan number, e.g. 018")
    parser.add_argument("--milestone", help="milestone, e.g. M2")
    parser.add_argument("--title", help="what this check is about, one line")
    parser.add_argument("--look", action="append", default=[], help="one thing to look at (repeat)")
    parser.add_argument("--step", action="append", default=[],
                        help='a step: "<text>", "<text> | <image>" or "<text> | <image> | x,y" (click ring, percent)')
    parser.add_argument("--image", action="append", default=[], help='a screenshot: "<image>" or "<image> | <caption>"')
    parser.add_argument("--reference", action="append", default=[], help='a reference: "<image> | <caption>"')
    parser.add_argument("--expected", help="what it should look like or do")
    parser.add_argument("--seen", help="what the critic saw")
    parser.add_argument("--again", type=int, help="this point re-checks an earlier one after a fix")
    parser.add_argument("--blocking", action="store_true", help="the work cannot continue without this answer")
    parser.add_argument("--ok", type=int, nargs="+", default=[], help="points the user accepted")
    parser.add_argument("--fix", nargs=2, action="append", default=[], metavar=("N", "WHAT"),
                        help="a point the user wants fixed, and what")
    args = parser.parse_args()
    project = args.project.resolve()

    if args.add:
        if not args.title or not args.look:
            parser.error("--add needs --title and at least one --look")
        result = add(project, args)
    elif args.rate:
        if not args.ok and not args.fix:
            parser.error("--rate needs --ok and/or --fix")
        for n, _ in args.fix:
            if not n.isdigit():
                parser.error(f"--fix: not a point number: {n}")
        result = rate(project, args.ok, args.fix)
    else:
        result = listing(project)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
