# Review findings as the input of a plan

For an input with code-review findings: a `stuck` section `## M<n> code-review` or `## final-review`, or a `review`. Also for every `deferred`, whatever it holds: review findings, observations from a manual check, or a `fix` deferred earlier (the PRD may have changed since). A `## plan gate` or `## qa` section is planned as before. Reviews of free-form input always find one more case; a plan that takes every leftover finding ends in the same stuck gates. The judge decides what is worth a plan, not the user and not you.

## Before writing the plan

1. List every finding still open in those sections, with its source (e.g. `012 #3`), `file:line` and category. Check each against the code as it is now; one already fixed gets one line under the input's `## Resolution`, never in the plan.
2. **Suggestions** (no change in behaviour: duplicated constants, docstrings, double parsing, dead code, speed) and **Unrealistic** findings (`gates.md` in `loc-orchestrate`) do not go to the judge and never into the plan. Speed comes back only when the user reports that something is noticeably slow. An observation from a manual check has no category: it was seen in real use, so it is never a suggestion or unrealistic; it goes to the judge as Non-blocking, with the `file:line` it names, if any.
3. Give the Blocking and Non-blocking ones to the `judge` agent, with the plan they came from (the input's `**Source:**`; none → `loc/PRD.md` and `Invariants` only), `loc/PRD.md` and `CLAUDE.md`. `fix` goes into the plan; `enough` does not. Never overrule a verdict, and never ask the user which findings to take: the report shows the `enough` ones, and the user may answer `popraw N`.

## Where they are recorded

In the new plan's `## Review notes` (before `## Resolution`), one line each, gate `planning`. Only these three forms; `check_state.py` rejects anything else there:

```
- enough (planning): 012 #3 `parse.py:41` — "around five" gives an approximate 17:00. Reason: same part of day, the hour is marked approximate [Goal 2]
- suggestion (planning): 012 #6 `app.py:98` — the constant repeats the list from `text.py`
- unrealistic (planning): 013 #2 `app.py:240` — `force=False`. Who produces it: no caller in the code passes this value
- enough (planning): 014 #3 — the model added its own heading above the list. Reason: cosmetic, the list itself is correct [plan Goal]
```

The last form is an observation from a manual check: no `file:line` when it names none.

`## Out of scope` gets: `Input findings without a fix verdict: ## Review notes.` In the plan's gate, a critic finding that repeats one of these lines goes to `## Risks and decisions` citing the verdict and is not blocking. Reviews of the plan later see the lines, so a finding judged here is not raised again without a new argument.

**No `fix` at all**: write no plan. Under the input's `## Resolution` write `→ no plan (<date>): the judge gave no fix`, then the lines; close it like any input (`references/closing.md`, steps 2–3). The journal entry points to `loc/inbox/done/<input>`. The report numbers the `enough` lines and ends without an orchestrate step.

**No `deferred` file** for any of these lines. An `deferred` is only for a `fix` finding deliberately left out of the plan, with the reason.
