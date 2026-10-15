# Review findings as the input of a plan

For an input with code-review findings: a `utknelo` section `## M<n> code-review` or `## final-review`, or a `przeglad`. Also for every `odlozone`, whatever it holds: review findings, observations from a manual check, or a `fix` deferred earlier (the PRD may have changed since). A `## bramka planu` or `## qa` section is planned as before. Reviews of free-form input always find one more case; a plan that takes every leftover finding ends in the same stuck gates. The judge decides what is worth a plan, not the user and not you.

## Before writing the plan

1. List every finding still open in those sections, with its source (e.g. `012 #3`), `file:line` and category. Check each against the code as it is now; one already fixed gets one line under the input's `## Rozstrzygnięcie`, never in the plan.
2. **Suggestions** (no change in behaviour: duplicated constants, docstrings, double parsing, dead code, speed) and **Unrealistic** findings (`gates.md` in `loc-orchestrate`) do not go to the judge and never into the plan. Speed comes back only when the user reports that something is noticeably slow. An observation from a manual check has no category: it was seen in real use, so it is never a suggestion or unrealistic; it goes to the judge as Non-blocking, with the `file:line` it names, if any.
3. Give the Blocking and Non-blocking ones to the `judge` agent, with the plan they came from (the input's `**Źródło:**`; none → `loc/PRD.md` and `Invariants` only), `loc/PRD.md` and `CLAUDE.md`. `fix` goes into the plan; `enough` does not. Never overrule a verdict, and never ask the user which findings to take: the report shows the `enough` ones, and the user may answer `popraw N`.

## Where they are recorded

In the new plan's `## Uwagi z przeglądów` (before `## Rozstrzygnięcie`), one line each, gate `planowanie`. Only these three forms; `check_state.py` rejects anything else there:

```
- dość (planowanie): 012 #3 `parse.py:41` — „koło piątej” daje 17:00 przybliżoną. Powód: pora dnia ta sama, godzina oznaczona jako przybliżona [Cel 2]
- sugestia (planowanie): 012 #6 `app.py:98` — stała powtarza listę z `text.py`
- nierealna (planowanie): 013 #2 `app.py:240` — `force=False`. Kto to wytwarza: żaden wołający w kodzie nie podaje tej wartości
- dość (planowanie): 014 #3 — model dopisał nad listą własny nagłówek. Powód: kosmetyka, treść listy poprawna [plan Cel]
```

The last form is an observation from a manual check: no `file:line` when it names none.

`## Czego nie robimy` gets: `Uwagi z wejścia bez werdyktu fix: ## Uwagi z przeglądów.` In the plan's gate, a critic finding that repeats one of these lines goes to `## Ryzyka i decyzje` citing the verdict and is not blocking. Reviews of the plan later see the lines, so a finding judged here is not raised again without a new argument.

**No `fix` at all**: write no plan. Under the input's `## Rozstrzygnięcie` write `→ bez planu (<date>): sędzia nie dał fix`, then the lines; close it like any input (`references/closing.md`, steps 2–3). The journal entry points to `loc/inbox/done/<input>`. The report numbers the `dość` lines and ends without an orchestrate step.

**No `odlozone` file** for any of these lines. An `odlozone` is only for a `fix` finding deliberately left out of the plan, with the reason.
