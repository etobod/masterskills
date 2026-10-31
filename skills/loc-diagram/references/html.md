# The HTML version of a diagram

`loc/diagrams/<slug>.html` (or `tmp/<slug>.html`) shows the same diagram as the `.md` beside it, drawn as SVG for the browser. The `.md` stays the record; write the HTML right after it, from the same boxes and arrows, never from a second reading of the code.

## The page

- **One self-contained file**: inline `<style>` and inline `<svg>`, no scripts, fonts or images from the network, so it opens offline from disk.
- `<title>` and an `<h1>`: the topic. Under it: the commit and date from the `.md`, and the sources.
- **Colours** as CSS variables on `:root`, with a dark set under `@media (prefers-color-scheme: dark)`; `body` has its own background. Boxes, arrows and text take their colours from the variables, never fixed in the SVG.
- **Layout** as in the terminal diagram: the same boxes in the same order and direction, so the user can switch between the two without getting lost. Give the SVG a `viewBox` and `width: 100%`, so it scales with the window.

## Shapes

| Terminal | SVG |
|---|---|
| box: name, `file:line`, what it does | `<rect rx="6">` with three `<text>` lines: the name bold, `file:line` in monospace, the description smaller |
| `◇ condition?` with branches | a `<polygon>` diamond, one labelled arrow per branch |
| `[ store ]` | a cylinder (`<ellipse>` + `<rect>`) or a rectangle with a double top line |
| `──▶` labelled | `<line>` or `<path>` with an arrowhead `<marker>`, the label on a background-coloured `<rect>` so the line does not cross it |
| `─ ─▶` async | the same with `stroke-dasharray` |
| `(1)`, `(2)` | a small circle with the number at the start of the arrow |
| `?` unconfirmed | a dashed box border and the `?` beside the name |

Size each box to its longest line (about 7.5 px per character at 13 px monospace) plus padding, and keep at least 40 px between boxes so labels fit.

## Under the SVG

The walk-through, "not shown" and "where to look first" from the `.md`, as HTML lists. Every `file:line` is in `<code>`.

## Check before giving the path

- Every box and arrow of the `.md` is in the SVG, and nothing else.
- No label overlaps a box or another label: compare their `x`, `y`, width and height.
- The file has no `http://` or `https://` other than in text.
