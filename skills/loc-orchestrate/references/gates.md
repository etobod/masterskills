# Review gates, stuck gates and follow-up files

## Severity

Every finding of a milestone's code-review and of the final review gets one severity:

- **Blocking**: wrong behaviour, a broken `Invariants` entry, a criterion not met. code-review `high`.
- **Non-blocking**: a real defect in a rarer case. code-review `medium`.
- **Suggestion**: everything else: style, wording, an unlikely edge case. code-review `low`.

When code-review gives no severity, judge it by these definitions; do not lower one to pass the gate. A review gate fixes Blocking and Non-blocking findings and **passes when a round has none left**. Suggestions are **not fixed** in the gate: fixing them round after round widens the plan and never ends. A milestone's Suggestions go to the plan's deferred file; the final review's go to a file of their own (below).

## The deferred file

One per plan. At the first Suggestion create it and record its path in the state file's `deferred`:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type odlozone --slug "<plan topic> drobne uwagi" --title "<plan> — drobne uwagi z przeglądów" --source "<plan path>"
```

Under `## Co odłożono` one line per finding: `file:line`, the gate (`M2 code-review`, `final-review`), the finding verbatim, the suggested fix; later Suggestions are added there. `## Dlaczego nie teraz`: Suggestions from review gates, not fixed in the gate. `## Kiedy wrócić`: when that code is next changed.

The final review's Suggestions go to a separate `odlozone` file (`--slug "<plan topic> przegląd końcowy"`, same sections), not to `deferred`: the deferred file then holds only milestone points and can close when they are resolved.

## Stuck gate

Do not start a fourth round, and **change no more code**: a fix after the last round is never reviewed. What remains goes into the file:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type utknelo --slug "<plan topic> m<n> <gate>" --title "<plan> — M<n>, <gate>" --source "<plan path>"
```

Fill every section: the gate and milestone; for each round the verbatim failure output (even when it repeats the last one), what you changed and the result; `## Co zostało`, each point with `file:line`; whether the rounds went in circles; and which version of the code the work continued with. Record its path in the gate's `stuck`, set the milestone to `stuck`, and go on with the next milestone.

## Closing what the plan resolved

After the final review, before closing the plan, take every file named in a milestone gate's `stuck` (`M<n>/…`) and in `deferred` that is still in `loc/inbox/`. Check each point of its `## Co zostało` (`utknelo`) or `## Co odłożono` (`odlozone`) against the code as it is now: a later milestone or the final review may have fixed it.

- **Every point resolved**: under `## Rozstrzygnięcie` write `rozwiązane w planie <NNN>` and, per point, what fixed it with `file:line`; set `**Status:** zamknięte <date>`; `mv` it to `loc/inbox/done/`.
- **Some resolved**: mark those points `✅ rozwiązane w planie <NNN>: file:line` and leave the file open.
- **None**: leave it as it is.

The files of the `qa` and `final-review` gates stay open: nothing reviews after them. The plan's `## Rozstrzygnięcie` names each file closed here, e.g. `M1 ✅ (utknelo 004 zamknięte: rozwiązane w M2)`.
