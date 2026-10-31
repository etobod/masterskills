---
name: loc-diagram
description: Use when the user asks how something in the project works or flows ("how does saving an entry work", "jak dziala zapis wpisu", "show the flow of X", "skad sie bierze Y", "co sie dzieje po Z", "loc-diagram <topic>"), and for "loc-diagram overview" at the end of a plan. Draws a terminal diagram from the code, with file:line on every box, keeps it in loc/diagrams/ and updates it when asked again.
argument-hint: "<what to explain, e.g. saving an entry> | overview"
---

# loc-diagram

A paragraph makes the user rebuild the picture in their head; draw it for them, **from the code read now**, never from memory, a plan or `loc/MEMORY.md`.

## 1. Find the diagram

Diagrams live in `loc/diagrams/`, one Markdown file per topic, `<slug>.md` (e.g. `saving-an-entry.md`):

| Where | What |
|---|---|
| `loc/diagrams/overview.md` | always kept: the whole project from above, refreshed by `loc-orchestrate` at the end of every plan |
| `loc/diagrams/<slug>.md` | also kept: the topics listed under `## Diagrams` in the project's `CLAUDE.md` |
| `loc/diagrams/tmp/<slug>.md` | every other question |

Look for a file on the same topic in both places first (its title and `**Asked as:**` lines). One exists: run `git diff --stat <its commit> -- <its sources>`. Nothing changed: show it as it is and add the question to `**Asked as:**`. Something changed: redraw it in the same file. None exists: draw a new one in `tmp/`. When the user says to keep one ("na stale", "keep it"), move it out of `tmp/` and add its topic under `## Diagrams` in `CLAUDE.md`.

A file is a picture of the code at one commit, never a source of truth: code wins, and a diagram that disagrees with it is redrawn, not believed.

## 2. Read the path

1. Find the entry point (command, handler, hook, function). Grep for it; do not guess.
2. Follow it to the end: every call that matters, every file or table it reads or writes, every branch that changes the outcome, every process or agent it hands over to. Note `file:line` for each.
3. Across more than about ten files, send the `Explore` agent for the map first and read only the steps it names.
4. What you could not confirm (a dynamic call, a runtime config, a service outside the project) is marked `?` and named under the diagram.

**Overview**: the parts of the project (apps, services, modules, stores, external systems) and what flows between them, read from the entry points, the top-level directories and the manifests. At the end of a plan, redraw it only when the plan added, removed or renamed a part or a flow between parts; otherwise only update its commit. Its header also has `**Plugin:** <version>`: keep it, unless the session-start note names a new one.

## 3. Draw it

One fenced block marked `text`, built from these pieces only:

```text
┌─────────────────┐      ◇ cap reached?          [ entries table ]
│ name()          │       ├─ yes → stop report    a file, table or other store
│ file.py:42      │       └─ no  → next step
└─────────────────┘
──▶  call or data flow, labelled with what passes      ─ ─▶  async: a job, an agent, a hook
```

- **Boxes** are steps: the name as in the code, then `file:line`, then optionally what it does in the user's language.
- **Arrows** go top to bottom or left to right, labelled with what passes or the condition; number them `(1)`, `(2)`… when the order is not obvious.
- **At most 100 columns and about 40 lines.** A larger flow becomes an overview plus one diagram per part, titled `Part 2: <name>`.
- **Count the columns**: every box edge lines up; no tabs, emoji or wide characters inside boxes.
- **One level of detail** per diagram. Leave out logging, retries and error paths unless asked; say so.

## 4. Write the file and answer

The file:

```markdown
# Saving an entry
**Commit:** <short hash of HEAD>, <date>
**Sources:** api/entries.py, core/rules.py, db/store.py
**Asked as:** how does saving an entry work?

<the diagram>

<walk-through, not shown, where to look first>
```

Under the diagram, in the user's language:

1. **Walk-through**: one line per numbered arrow or box: what happens and why, with `file:line`.
2. **Not shown**: what you left out, and every `?` with what would confirm it.
3. **Where to look first** when changing it: one or two `file:line`.

Answer with the diagram and those three, shorter than it, then the file path. When asked for more detail on one box, draw that box as its own diagram, the same way.

**HTML**: the overview, every kept diagram, and any diagram the user asks to see in the browser ("w przegladarce", "html") also get `<slug>.html` beside the `.md`; follow `references/html.md`. Give the user the path to open.

