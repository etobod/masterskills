# Review gates, stuck gates and follow-up files

## Categories

Every finding of a milestone's code-review and of the final review gets one category:

- **Blocking** (`blokująca`): wrong behaviour, a broken `Invariants` entry, a criterion not met. code-review `high`.
- **Non-blocking** (`nieblokująca`): a real defect in a rarer case that does happen. code-review `medium`.
- **Suggestion** (`sugestia`): real but minor: style, wording, a comment in the wrong place. code-review `low`.
- **Unrealistic** (`nierealna`): the finding needs an input or a state that **nothing in this project produces**: not its code, not its real data, not a user mistake you can foresee. Ask "who or what here would produce this?" and name the answer: the code that writes that input and why it never writes this form (e.g. "the report is written by the model following `report-format.md`, which uses no numeric entities"). If you cannot name it, the finding is not unrealistic.

When code-review gives no severity, judge it by these definitions; never lower one to pass the gate. A finding keeps its category from the milestone to the final review unless there is a new argument, such as naming who produces the input. A review gate fixes Blocking and Non-blocking findings and **passes when a round has none left**. Suggestions and Unrealistic findings are **never fixed in the gate**: fixing them round after round widens the plan and never ends.

## Review notes in the plan

Suggestions and Unrealistic findings create **no inbox file**. Each becomes one line in the plan file, in a section `## Uwagi z przeglądów` placed right before `## Rozstrzygnięcie` (create it at the first note):

```
- sugestia (M2 code-review): `app.py:14` — komentarz LINE_PREFIX stoi nad RAW_HTML
- nierealna (final-review): `check.py:88` — encja `&#51;` w raporcie pokaże 3, a liczy 51. Kto to wytwarza: raport pisze model według report-format.md, który nie używa encji
```

The gate is `M<n> code-review` or `final-review`. Only the finding: no proposed fix, no "when to come back". An Unrealistic line ends with `Kto to wytwarza:` and the answer; `check_state.py` rejects the section otherwise.

A run started on an older version may have a `deferred` `odlozone` file in the state file: keep appending its milestone Suggestions there, and close it as below.

## Stuck gate

Do not start a fourth round, and **change no more code**: a fix after the last round is never reviewed. What remains goes into the file:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type utknelo --slug "<plan topic> m<n> <gate>" --title "<plan> — M<n>, <gate>" --source "<plan path>"
```

Fill every section: `**Kategoria:**` (`blokująca` or `nieblokująca`: the most serious finding left; a failing proof, red or QA gate is `blokująca`); the gate and milestone; for each round the verbatim failure output (even when it repeats the last one), what you changed and the result; `## Co zostało`, each point with `file:line`; whether the rounds went in circles; and which version of the code the work continued with. Record its path in the gate's `stuck`, set the milestone to `stuck`, and go on with the next milestone.

## Closing what the plan resolved

After the final review, before closing the plan, take every file named in a milestone gate's `stuck` (`M<n>/…`) and in `deferred` that is still in `loc/inbox/`. Check each point of its `## Co zostało` (`utknelo`) or `## Co odłożono` (`odlozone`) against the code as it is now: a later milestone or the final review may have fixed it.

- **Every point resolved**: under `## Rozstrzygnięcie` write `rozwiązane w planie <NNN>` and, per point, what fixed it with `file:line`; set `**Status:** zamknięte <date>`; `mv` it to `loc/inbox/done/`.
- **Some resolved**: mark those points `✅ rozwiązane w planie <NNN>: file:line` and leave the file open.
- **None**: leave it as it is.

The files of the `qa` and `final-review` gates stay open: nothing reviews after them. The plan's `## Rozstrzygnięcie` names each file closed here, e.g. `M1 ✅ (utknelo 004 zamknięte: rozwiązane w M2)`.
