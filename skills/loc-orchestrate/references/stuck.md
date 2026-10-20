# Stuck gates and closing what the plan resolved

## Stuck gate

Do not start a fourth round, and **change no more code**: a fix after the last round is never reviewed. **One `stuck` file per plan run**: the first stuck gate creates it, each later one adds its own section to it. Its path is in the `stuck` field of any gate in `loc/state/<NNN>.json`; none yet → create it. Create it once:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type stuck --slug "<plan topic>" --title "<plan> — stuck gates" --source "<plan path>"
```

Per gate, one section `## M<n> <gate>` (or `## qa`, `## final-review`) with: for each round the verbatim failure output (even when it repeats the last one), what you changed and the result; `### What remains`, each point with `file:line`; whether the rounds went in circles; and which version of the code the work continued with. `**Category:**` is the most serious finding left in the whole file (`blocking` or `non-blocking`; a failing proof, red or QA gate is `blocking`); raise it when a later section is worse. Record its path in the gate's `stuck`, set the milestone to `stuck`. Call the `architect` agent in Challenge mode with this section, the plan path, `loc/PRD.md` and `CLAUDE.md`; when it recommends anything but keeping every decision, turn its report into a `question` file as in `gates.md`. Then go on with the next milestone.

## Final review triage

A `final-review` gate that went stuck is not left as it is. Call the `architect` agent in Triage mode with the stuck file's `## final-review` section, the plan path, `loc/PRD.md` and `CLAUDE.md`. Append its recommended verdict to the gate's `triage` list, then:

- **retry**: call `loc-review` again for rounds 4–6 (once per plan). It adds a `## final-review (rounds 4–6)` section; when that fails too, call the architect again: now only `plan` or `ask`.
- **plan**: the points of `### What remains` become work for `loc-planning`:
  `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type deferred --slug "<plan topic> final review" --title "<plan> — final review leftovers" --source "<stuck path>" --what "<each point with file:line>" --why "<the architect's reason>" --when "the next loc-planning"`
- **ask**: the user decides: `next_number.py --type question --title "Final review of plan <NNN>: <topic>" --source "<stuck path>"`, in the user's language: what is at stake with `file:line`, the architect's options with the recommended one first, and its reason.

Name the new file in the plan's `## Resolution` and in the report. The plan then closes as usual.

## Closing what the plan resolved

After the final review, before closing the plan, take every file named in a milestone gate's `stuck` (`M<n>/…`) and in `deferred` that is still in `loc/inbox/`. Check each point of its `### What remains` (`stuck`) or `## What was deferred` (`deferred`) against the code as it is now: a later milestone or the final review may have fixed it.

- **Every point resolved**: under `## Resolution` write `resolved in plan <NNN>` and, per point, what fixed it with `file:line`; set `**Status:** closed <date>`; `mv` it to `loc/inbox/done/`.
- **Some resolved**: mark those points `✅ resolved in plan <NNN>: file:line` and leave the file open.
- **None**: leave it as it is.

Points in a `## qa` or `## final-review` section stay open: nothing reviews after them. The plan's `## Resolution` names each file closed here, e.g. `M1 ✅ (stuck 004 closed: resolved in M2)`.
