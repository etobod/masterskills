---
name: loc-planning
description: Use when the user asks for a plan, or to turn a brainstorm, review, deferred item, stuck gate, answered question or PRD fragment into one (e.g. "loc-planning 004", "make a plan from the brainstorm"). Writes a plan with milestones and automatic proofs to loc/inbox/ and gates it. Never executes the plan.
argument-hint: "<inbox number or file | PRD fragment | task text>"
---

# loc-planning

Turns an input into `loc/inbox/NNN-plan-<topic>.md`: a plan someone can execute without deciding anything. Plans are made only here and executed only by `loc-orchestrate`.

**Do not execute the plan, do not change code.**

## 1. Input

`$ARGUMENTS` is one of:

- **An inbox number or file**: `brainstorm`, `przeglad`, `odlozone`, `utknelo`, or a `pytanie` that already has an answer under `## Rozstrzygnięcie`. The number is enough; find the file in `loc/inbox/`.
- **A fragment of `loc/PRD.md`**, named by its heading.
- **Plain text**: the task itself.

No argument: if `loc/inbox/` has exactly one `brainstorm`, use it; otherwise ask what to plan. An open `pytanie` is not an input: the user has not answered it yet.

## 2. Read the code, not documents about it

1. The input, the project's `CLAUDE.md` (`Commands` gives the proof commands; `Invariants`, `Limits`, `Manual verification / UAT`) and `loc/PATTERNS.md` (entries whose **Kiedy stosować** matches).
2. The code the change touches. For more than a couple of files, delegate to the `researcher` agent with the question "what exists today for <change>" and use its `file:line` report. Documents and old plans are not evidence; code is.
3. If the project has no `CLAUDE.md` `Commands` section, say so in the plan's risks and use the commands you verified by running them. A run leaves no files behind: nothing new in `git status --short` (Python: `python -B`).

## 3. Unknowns become questions, not holes

Anything the user must decide goes to its own `pytanie` file **before** the plan is written: first look for a similar open one and extend it; otherwise create one with the script (below) and fill it completely (context, options with cost, recommendation). The plan then proceeds on the recommendation and says so in `## Ryzyka i decyzje` (`→ loc/inbox/NNN-pytanie-…`, tymczasowo wariant A). Stop without a plan only if that interim choice would be expensive to undo.

## 4. Write the plan

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type plan --slug "<topic>" --title "<title>" --source "<input file or PRD heading or rozmowa>"
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

The file comes from the template with all sections. Fill them in Polish:

- **Cel**: what works afterwards, in terms the user can check.
- **Czego nie robimy**: what is deliberately out of scope.
- **Nie bronimy przed**: who produces inputs the code deliberately does not defend against, with the reason (e.g. an administrator who could disable the tool anyway). Never a foreseeable user mistake. `- brak` when nothing. Reviews call such inputs Unrealistic.
- **Kontekst z kodu**: the files and `file:line` the plan relies on, as read now.
- **Kamienie milowe**: `### M1 — <name>`, `### M2 …`. Each is a working, reviewable piece with exactly one `**Dowód:**` line: a command and its expected result that **fails if the milestone is not done**. Optional `**Sprawdzenie ręczne:**` per `Manual verification / UAT`. Code and its tests go in the same milestone; for code, criteria, tests and performer follow `references/tests.md`. A milestone's product is never a decision, an audit or a question.
- **Ryzyka i decyzje**: references to brainstorm decisions (`B-01`…) and `pytanie` files, and what each risk would cost.

Keep it proportional: a small change gets one or two milestones.

## 5. Gate: at most 3 rounds

Each round, recorded as one line in `## Bramka planu`:

1. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py <plan>` must exit `0`. Fix every issue it lists.
2. The `rubber-duck` agent with **what was asked** (the input file, or the PRD fragment or text) and **what was produced** (the plan path). Fix every Blocking and Non-blocking finding; a finding you reject goes into `## Ryzyka i decyzje` with the reason.

The round passes when the script exits `0` and the critic reports nothing blocking. After a failed third round: set the plan's `**Status:**` to `otwarte — bramka nie przeszła`, create a `utknelo` file with all three rounds and the remaining issues, and report. Do not start a fourth round.

## 6. Close the input

Follow `references/closing.md` for the input's type: the input file gets its `## Rozstrzygnięcie` and moves to `loc/inbox/done/`, a PRD fragment gets the `→ przekazane` marker; then the journal entry.

## 7. Report

In the user's language, briefly:

- the plan's path and its milestones, one line each;
- the `Nie bronimy przed` list, for the user to accept before execution;
- the gate result (rounds, "skan czysty, krytyk bez uwag blokujących", or what remains and the `utknelo` file);
- new `pytanie` files, each with its question in one line;
- what moved to `loc/inbox/done/`.

End with the next step: `/masterskills:loc-orchestrate <NNN>` when the user decides. Do not start it.
