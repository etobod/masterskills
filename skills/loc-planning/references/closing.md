# Closing the input of a plan

Done after the plan passes the gate (or ends in `utknelo`). Take the time with `date "+%Y-%m-%d"`; never write it from memory. Move files with `mv` (`loc/` is not in git). Nothing is ever deleted.

## Input file in `loc/inbox/`

For a `brainstorm`, `przeglad`, `odlozone`, `utknelo` or an answered `pytanie`:

1. Under `## Rozstrzygnięcie` write: `→ plan loc/inbox/NNN-plan-<topic>.md (<date>)`. For a `przeglad`, add every finding the plan does not fix, each with the reason and where it goes instead (usually a new `odlozone` file). Never rewrite the original content.
2. Set `**Status:**` to `zamknięte <date>`.
3. Move the file to `loc/inbox/done/` under the same name.
4. In the plan's `**Źródło:**`, point to the new location: `loc/inbox/done/<name>`.

A `pytanie` whose `## Rozstrzygnięcie` is empty is not closed: it stays open in `loc/inbox/`, and the plan only refers to it.

## Fragment of `loc/PRD.md`

Move it into the plan and remove it from the PRD: `references/prd.md`.

## Plain text

Nothing to close. The plan's `**Źródło:**` says `rozmowa` with a one-line summary of the request.

## Journal entry

After closing the input, one command adds the entry to `loc/MEMORY.md` (Polish, at most 3 sentences: what was planned, from which input, the gate result):

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type Planowanie --title "<title>" --text "<sentences> Szczegóły: loc/inbox/NNN-plan-<topic>.md"
```

Run it exactly as written, on its own. No `loc/MEMORY.md`: skip it.

## Plan that did not pass the gate

Close the input the same way, so the next attempt starts from the plan and the `utknelo` file rather than from a stale brainstorm. The `utknelo` file's `**Źródło:**` names the plan.
