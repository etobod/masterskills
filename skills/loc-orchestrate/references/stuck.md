# Stuck gates and closing what the plan resolved

## Stuck gate

Do not start a fourth round, and **change no more code**: a fix after the last round is never reviewed. **One `utknelo` file per plan run**: the first stuck gate creates it, each later one adds its own section to it. Its path is in the `stuck` field of any gate in `loc/state/<NNN>.json`; none yet → create it. Create it once:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type utknelo --slug "<plan topic>" --title "<plan> — utknięte bramki" --source "<plan path>"
```

Per gate, one section `## M<n> <gate>` (or `## qa`, `## final-review`) with: for each round the verbatim failure output (even when it repeats the last one), what you changed and the result; `### Co zostało`, each point with `file:line`; whether the rounds went in circles; and which version of the code the work continued with. `**Kategoria:**` is the most serious finding left in the whole file (`blokująca` or `nieblokująca`; a failing proof, red or QA gate is `blokująca`); raise it when a later section is worse. Record its path in the gate's `stuck`, set the milestone to `stuck`, and go on with the next milestone.

## Closing what the plan resolved

After the final review, before closing the plan, take every file named in a milestone gate's `stuck` (`M<n>/…`) and in `deferred` that is still in `loc/inbox/`. Check each point of its `### Co zostało` (`## Co zostało` in older files) (`utknelo`) or `## Co odłożono` (`odlozone`) against the code as it is now: a later milestone or the final review may have fixed it.

- **Every point resolved**: under `## Rozstrzygnięcie` write `rozwiązane w planie <NNN>` and, per point, what fixed it with `file:line`; set `**Status:** zamknięte <date>`; `mv` it to `loc/inbox/done/`.
- **Some resolved**: mark those points `✅ rozwiązane w planie <NNN>: file:line` and leave the file open.
- **None**: leave it as it is.

Points in a `## qa` or `## final-review` section stay open: nothing reviews after them. The plan's `## Rozstrzygnięcie` names each file closed here, e.g. `M1 ✅ (utknelo 004 zamknięte: rozwiązane w M2)`.
