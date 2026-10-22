# Stuck gates and closing what the plan resolved

## Stuck milestone or QA gate

Do not start a fourth round, and **change no more code**: a fix after the last round is never reviewed. No inbox file and no architect now: the record goes into the plan, and the architect weighs it once, in the triage at the end. Add the plan's section `## Stuck gates` above `## Resolution` if it has none, then one subsection per gate:

```
### M2 code-review
**Remains:**
- `parse.py:41` — "around five" still parses as 05:00
**Rounds:**
1. <the failure output word for word>; changed <what>; <result>
2. <the same, even when it repeats round 1>
3. <…>
**Continued with:** <which version of the code the work went on with>; rounds went in circles: <yes or no>
**Architect (Triage):** <filled at the end>
```

The heading is `### M<n> <gate>` or `### qa`. Set the gate's `stuck` to `"plan"` and the milestone to `stuck`, then go on with the next milestone. A later milestone may fix a point; it is checked against the code after the final review.

## Stuck final review or plan gate

The final review (`loc-review`) and the plan gate (`loc-planning`) still write a `stuck` file: their record must outlive the plan. One per plan run; the first creates it, a later one adds its section:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type stuck --slug "<plan topic>" --title "<plan> — stuck gates" --source "<gate, e.g. final-review> of <plan path>" --by "<the skill running: loc-review or loc-planning>"
```

Per gate, add it to `**Stuck gates:**` and write one section (`## final-review`, `## plan gate`) in the template's order: `**Gate:**`, `**Architect (Triage):**`, `**Next:**`, then `### What remains` with `file:line`, each round's verbatim output, what changed and the result, and whether the rounds went in circles. `**Category:**` is the most serious finding left in the file (a failing proof, red or QA gate is `blocking`). Record the path in the gate's `stuck`.

## Plan gate

`loc-planning` writes the `## plan gate` section with all rounds and what remains, then calls the `architect` agent in Triage mode with it, the plan, `loc/PRD.md` and `CLAUDE.md`:

- **retry**: rounds 4–6, once; when they fail too, Triage again: only plan or ask.
- **plan**: `**Status:**` → `open — gate failed`; the stuck file waits for the next planning, which starts from it.
- **ask**: as plan, plus `next_number.py --type question --source "<stuck file>" --by "architect (Triage)"` with its options.

## Closing what the plan resolved

After the final review, check each point of `**Remains:**` in the plan's `## Stuck gates` against the code as it is now: a later milestone or the final review may have fixed it. Mark a fixed one `- ✅ resolved in M3: <file:line>`. For an older run whose milestone gate made a `stuck` file, do the same with its `### What remains`; when every point is resolved, write `resolved in plan <NNN>` under its `## Resolution`, set `**Status:** closed <date>` and `mv` it to `loc/inbox/done/`.

## Triage

Triage runs when the final review went stuck, **or** when a point of `## Stuck gates` is still open after the closing check, even though the final review passed. Call the `architect` agent in Triage mode with the plan's `## Stuck gates`, the stuck file's `## final-review` section if any, the plan path, `loc/PRD.md` and `CLAUDE.md`. Append its verdict to the `final-review` gate's `triage` list and write it with its reason in each `**Architect (Triage):**`, then:

- **retry**: call `loc-review` again for rounds 4–6 (once per plan), with the open points as findings to fix. It adds a `## final-review (rounds 4–6)` section; when that fails too, call the architect again: now only `plan` or `ask`.
- **plan**: the open points become work for the next planning:
  `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type deferred --slug "<plan topic> leftovers" --title "<plan> — leftovers" --source "<plan path>" --what "<each point with file:line>" --why "<the architect's reason>" --when "the next loc-planning" --by "loc-orchestrate (architect: plan)"`
- **ask**: only what the architect called beyond its competence: `next_number.py --type question --title "Plan <NNN>: <topic>" --source "<plan path>" --by "architect (Triage)"`, in the user's language: what is at stake with `file:line`, the architect's options with the recommended one first, and its reason.

Name the new file in `**Next:**` (stuck file), the plan's `## Resolution` and the report. The plan then closes as usual.
