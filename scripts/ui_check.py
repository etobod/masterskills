#!/usr/bin/env python3
"""See a page the way a user does: screenshots at set widths and mechanical checks of its look.

- `--detect`: which tools the machine has: {"playwright": bool, "scrapling": bool, "install": "<command>"}.
- `--url <address or file> --widths 375,768,1440 --out <dir> [--name page]`: a full-page screenshot
  per width, `<out>/<name>-<width>.png`. Used for the project's own pages and for references.
- `--check` (with `--url`): in the same run, measures the page at each width: horizontal scroll,
  text cut off in its box, text contrast below WCAG AA (4.5:1, large text 3:1; a background image
  or gradient behind the text is skipped), and no visible focus after Tab. Exit 1 on a defect.
- `--tokens <tokens file> --files <files...>`: raw colours (`#hex`, `rgb()`, `hsl()`) and `px` values
  in font-size, margin, padding and gap outside the tokens file (0 and 1px are allowed). No browser
  needed. Exit 1 on a defect.

Playwright (Python) is imported only when a page is opened; without it `--url` prints
{"error": "no playwright", "install": ...} and exits 2. The plugin itself needs only the standard library.

Prints JSON: {"shots": [...], "defects": [{"kind", "width", "selector", "value"} | {"kind", "file", "line", "value"}]}
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

INSTALL = "python -m pip install playwright && python -m playwright install chromium"
NORMAL, LARGE = 4.5, 3.0
SOURCE_TYPES = {".css", ".scss", ".sass", ".less", ".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte"}
COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(")
DECLARATION = re.compile(r"([A-Za-z-]+)\s*:\s*([^;{}\n]+)")
PX = re.compile(r"(?<![\w.])(\d*\.?\d+)px\b")
COMMENT = re.compile(r"/\*.*?\*/", re.S)


def detect() -> dict:
    return {"playwright": importlib.util.find_spec("playwright") is not None,
            "scrapling": importlib.util.find_spec("scrapling") is not None,
            "install": INSTALL}


def luminance(rgb) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg) -> float:
    """WCAG contrast of two sRGB colours (r, g, b in 0-255)."""
    high, low = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def minimum_ratio(size_px: float, weight: int) -> float:
    """Large text is 24px, or 18.66px (14pt) bold."""
    return LARGE if size_px >= 24 or (weight >= 700 and size_px >= 18.66) else NORMAL


def size_property(name: str) -> bool:
    name = name.replace("-", "").lower()
    return name.startswith(("margin", "padding")) or name in {"fontsize", "gap", "rowgap", "columngap"}


def token_defects(tokens: Path, files: list) -> list:
    defects = []
    tokens = tokens.resolve()
    for path in files:
        path = Path(path)
        if path.resolve() == tokens or path.suffix.lower() not in SOURCE_TYPES or not path.is_file():
            continue
        text = COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), path.read_text(encoding="utf-8", errors="replace"))
        for number, line in enumerate(text.splitlines(), 1):
            for match in DECLARATION.finditer(line):
                name, value = match.group(1), match.group(2).strip().strip("'\",")
                if COLOUR.search(value):
                    defects.append({"kind": "raw-colour", "file": path.as_posix(), "line": number,
                                    "value": f"{name}: {value}"})
                elif size_property(name) and any(float(px) not in (0, 1) for px in PX.findall(value)):
                    defects.append({"kind": "raw-size", "file": path.as_posix(), "line": number,
                                    "value": f"{name}: {value}"})
    return defects


PAGE_CHECKS = r"""
([normal, large]) => {
  const out = [];
  const root = document.documentElement;
  if (root.scrollWidth > window.innerWidth + 1)
    out.push({kind: "horizontal-scroll", selector: "html", value: `${root.scrollWidth}px wide in ${window.innerWidth}px`});
  const name = el => {
    if (el.id) return "#" + el.id;
    let s = el.tagName.toLowerCase();
    if (el.classList.length) s += "." + [...el.classList].slice(0, 2).join(".");
    const parent = el.parentElement;
    if (!parent || parent === document.body || parent === root) return s;
    const same = [...parent.children].filter(c => c.tagName === el.tagName);
    if (same.length > 1) s += `:nth-of-type(${same.indexOf(el) + 1})`;
    return name(parent) + " > " + s;
  };
  const rgba = text => {
    const m = text.match(/rgba?\(([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+%?))?\)/);
    if (!m) return null;
    let a = m[4] === undefined ? 1 : m[4].endsWith("%") ? parseFloat(m[4]) / 100 : parseFloat(m[4]);
    return [+m[1], +m[2], +m[3], a];
  };
  const over = (top, under) => top.slice(0, 3).map((c, i) => c * top[3] + under[i] * (1 - top[3])).concat(1);
  const lum = c => { const f = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
                     return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ratio = (a, b) => { const [h, l] = [lum(a), lum(b)].sort((x, y) => y - x); return (h + 0.05) / (l + 0.05); };
  const background = el => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const st = getComputedStyle(e);
      if (st.backgroundImage !== "none") return null;
      const c = rgba(st.backgroundColor);
      if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
    }
    return layers.reverse().reduce((under, top) => over(top, under), [255, 255, 255, 1]);
  };
  const visible = (el, st) => st.visibility !== "hidden" && st.display !== "none" && parseFloat(st.opacity) > 0
                              && el.getClientRects().length > 0;
  for (const el of document.body.querySelectorAll("*")) {
    if (out.length >= 60) break;
    const st = getComputedStyle(el);
    if (!visible(el, st) || ["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"].includes(el.tagName)) continue;
    const ownText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (["hidden", "clip"].includes(st.overflowX) && el.scrollWidth > el.clientWidth + 1 && el.textContent.trim())
      out.push({kind: "cut-off", selector: name(el), value: `${el.scrollWidth}px of text in ${el.clientWidth}px`});
    else if (["hidden", "clip"].includes(st.overflowY) && el.scrollHeight > el.clientHeight + 1 && el.textContent.trim())
      out.push({kind: "cut-off", selector: name(el), value: `${el.scrollHeight}px of text in ${el.clientHeight}px high`});
    if (!ownText) continue;
    const fg = rgba(st.color), bg = background(el);
    if (!fg || !bg) continue;
    const size = parseFloat(st.fontSize), weight = parseInt(st.fontWeight, 10) || 400;
    const need = size >= 24 || (weight >= 700 && size >= 18.66) ? large : normal;
    const got = ratio(over(fg, bg), bg);
    if (got < need)
      out.push({kind: "contrast", selector: name(el), value: `${got.toFixed(2)}:1, needs ${need}:1`});
  }
  return out;
}
"""

FOCUS_CHECK = r"""
() => {
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement) return null;
  // Element identity, not the selector: two `a.nav-link` are two stops, the same one twice is a cycle.
  const seen = window.__uiCheckSeen = window.__uiCheckSeen || new WeakSet();
  if (seen.has(el)) return {repeat: true};
  seen.add(el);
  const st = getComputedStyle(el);
  const outline = st.outlineStyle !== "none" && parseFloat(st.outlineWidth) > 0;
  const shadow = st.boxShadow && st.boxShadow !== "none";
  let s = el.id ? "#" + el.id : el.tagName.toLowerCase() + (el.classList.length ? "." + el.classList[0] : "");
  return {selector: s, text: (el.textContent || el.value || "").trim().slice(0, 30), visible: outline || shadow};
}
"""


def target_url(value: str) -> str:
    path = Path(value)
    return path.resolve().as_uri() if "://" not in value and path.exists() else value


def run_pages(url: str, widths: list, out, name: str, check: bool) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "no playwright", "install": INSTALL}
    result = {"shots": [], "defects": []}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as error:  # the package is there, the browser is not
            return {"error": f"no browser: {str(error).splitlines()[0]}", "install": "python -m playwright install chromium"}
        try:
            for width in widths:
                page = browser.new_page(viewport={"width": width, "height": 900})
                try:
                    page.goto(target_url(url), wait_until="load")
                except Exception as error:  # a timeout or a refused address: keep the JSON contract
                    return {"error": f"cannot open {url}: {str(error).splitlines()[0]}"}
                try:  # a page with a websocket or polling never goes idle; settle briefly, then go on
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                if out is not None:
                    out.mkdir(parents=True, exist_ok=True)
                    shot = out / f"{name}-{width}.png"
                    page.screenshot(path=str(shot), full_page=True)
                    result["shots"].append(shot.as_posix())
                if check:
                    for defect in page.evaluate(PAGE_CHECKS, [NORMAL, LARGE]):
                        result["defects"].append({**defect, "width": width})
                    for _ in range(15):
                        page.keyboard.press("Tab")
                        focus = page.evaluate(FOCUS_CHECK)
                        if focus is None or focus.get("repeat"):
                            break
                        if not focus["visible"]:
                            result["defects"].append({"kind": "no-focus", "width": width, "selector": focus["selector"],
                                                      "value": f"no outline or shadow on focus: {focus['text']!r}"})
                page.close()
        finally:
            browser.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detect", action="store_true", help="which tools the machine has")
    parser.add_argument("--url", help="a page address or a local HTML file")
    parser.add_argument("--widths", default="375,768,1440", help="viewport widths in px, comma separated")
    parser.add_argument("--out", type=Path, help="directory for the screenshots")
    parser.add_argument("--name", default="page", help="screenshot file name prefix")
    parser.add_argument("--check", action="store_true", help="measure scroll, cut-off text, contrast and focus")
    parser.add_argument("--tokens", type=Path, help="the project's tokens file")
    parser.add_argument("--files", nargs="+", default=[], help="source files to check against the tokens")
    args = parser.parse_args()

    if args.detect:
        print(json.dumps(detect()))
        return 0
    if not args.url and not args.tokens:
        parser.error("give --detect, --url or --tokens")
    if args.url and not (args.out or args.check):
        parser.error("--url needs --out (screenshots) and/or --check")
    result = {"shots": [], "defects": []}
    if args.tokens:
        if not args.files:
            parser.error("--tokens needs --files")
        result["defects"] += token_defects(args.tokens, args.files)
    if args.url:
        widths = [int(w) for w in args.widths.split(",") if w.strip()]
        pages = run_pages(args.url, widths, args.out, args.name, args.check)
        if "error" in pages:
            print(json.dumps(pages))
            return 2
        result["shots"] += pages["shots"]
        result["defects"] += pages["defects"]
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 1 if result["defects"] else 0


if __name__ == "__main__":
    sys.exit(main())
