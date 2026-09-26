# Closing the input of a plan

Done after the plan passes the gate (or ends in `utknelo`). Take the time with `date "+%Y-%m-%d"`; never write it from memory. Move files with `git mv` when they are tracked, `mv` otherwise. Nothing is ever deleted.

## Input file in `inbox/`

For a `brainstorm`, `przeglad`, `odlozone`, `utknelo` or an answered `pytanie`:

1. Under `## Rozstrzygnięcie` write: `→ plan inbox/NNN-plan-<topic>.md (<date>)`. For a `przeglad`, add every finding the plan does not fix, each with the reason and where it goes instead (usually a new `odlozone` file). Never rewrite the original content.
2. Set `**Status:**` to `zamknięte <date>`.
3. Move the file to `inbox/done/` under the same name.
4. In the plan's `**Źródło:**`, point to the new location: `inbox/done/<name>`.

A `pytanie` whose `## Rozstrzygnięcie` is empty is not closed: it stays open in `inbox/`, and the plan only refers to it.

## Fragment of `docs/PRD.md`

Directly under the fragment's heading, add one line:

```
→ przekazane do inbox/NNN-plan-<topic>.md (<date>)
```

Change nothing else in the PRD: no summary, no status, no milestone list. From now on the plan and the code are the truth for this fragment; the PRD fragment is history.

## Plain text

Nothing to close. The plan's `**Źródło:**` says `rozmowa` with a one-line summary of the request.

## Plan that did not pass the gate

Close the input the same way, so the next attempt starts from the plan and the `utknelo` file rather than from a stale brainstorm. The `utknelo` file's `**Źródło:**` names the plan.
