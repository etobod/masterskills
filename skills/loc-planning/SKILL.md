---
name: loc-planning
description: Use when the user asks for a plan, or to turn a brainstorm, review, deferred item, stuck gate, answered question or PRD fragment into one (e.g. "loc-planning 004", "make a plan from the brainstorm"). Writes a plan with milestones and automatic proofs to loc/inbox/ and gates it. Never executes the plan.
argument-hint: "<inbox number or file | PRD fragment | task text>"
---

# loc-planning

Turns an input into `loc/inbox/NNN-plan-<topic>.md`: a plan someone can execute without deciding anything.

**Do not execute the plan, do not change code.**

## 1. Input

`$ARGUMENTS` is one of:

- **An inbox number or file**: `brainstorm`, `review`, `deferred`, `stuck`, or a `question` that already has an answer under `## Resolution`. The number is enough; find the file in `loc/inbox/`. Review findings in it, or a `deferred`: `references/findings.md` first.
- **A fragment of `loc/PRD.md`**, named by its heading.
- **Plain text**: the task itself; `fix N`: the N-th `enough` line of the last report.

No argument: if `loc/inbox/` has exactly one `brainstorm`, use it; otherwise ask what to plan. An open `question` is not an input.

## 2. Read the code, not documents about it

1. The input, the project's `CLAUDE.md` (`Commands` gives the proof commands; `Invariants`, `Limits`, `Manual verification / UAT`) and `loc/PATTERNS.md` (entries whose **When to use** matches).
2. The code the change touches. For more than a couple of files, delegate to the `researcher` agent with the question "what exists today for <change>" and use its `file:line` report. Documents are not evidence; code is.
3. If the project has no `CLAUDE.md` `Commands` section, say so in the plan's risks and use the commands you verified by running them. A run leaves no files behind: nothing new in `git status --short` (Python: `python -B`).
4. Gaps in the frame: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/init_project.py --check` (writes nothing). Empty PRD sections: `references/prd.md`. Empty `CLAUDE.md` sections never stop you: what the plan can establish goes into a milestone, the rest into the report. Sections that contradict each other ("two separate chains" vs "one complex chain") become a `question` (step 3).

## 3. Unknowns become questions, not holes

Anything the user must decide goes to its own `question` file **before** the plan is written: first look for a similar open one and extend it; otherwise create one with the script (below) and fill it completely (context, options with cost, recommendation). The plan then proceeds on the recommendation and says so in `## Risks and decisions` (`→ loc/inbox/NNN-question-…`, tymczasowo wariant A). Stop without a plan only if that interim choice would be expensive to undo.

## 4. Write the plan

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type plan --slug "<topic>" --title "<title>" --source "<input file or PRD heading or conversation>"
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

The file comes from the template with all sections. Fill them in English:

- **Goal**: what works afterwards, in terms the user can check.
- **Out of scope**: what is deliberately out of scope.
- **Not defended against**: who produces inputs the code deliberately does not defend against, with the reason (e.g. an administrator who could disable the tool anyway). Never a foreseeable user mistake. `- none` when nothing. Reviews call such inputs Unrealistic.
- **Code context**: the files and `file:line` the plan relies on, as read now.
- **Milestones**: `### M1 — <name>`, `### M2 …`. Each is a working, reviewable piece with exactly one `**Proof:**` line: a command and its expected result that **fails if the milestone is not done**. Optional `**Manual check:**` per `Manual verification / UAT`. Code and its tests go in the same milestone; for code, criteria, tests and performer follow `references/tests.md`. A milestone's product is never a decision, an audit or a question.
- **Risks and decisions**: references to brainstorm decisions (`B-01`…) and `question` files, and what each risk would cost.

Small change, one or two milestones.

## 5. Gate: at most 3 rounds

Each round, recorded as one line in `## Plan gate`:

1. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py <plan>` must exit `0`. Fix every issue it lists.
2. The `rubber-duck` agent with **what was asked** (the input file, or the PRD fragment or text) and **what was produced** (the plan path). Fix every Blocking and Non-blocking finding; a finding you reject goes into `## Risks and decisions` with the reason.

The round passes when the script exits `0` and the critic reports nothing blocking. After a failed third round: set the plan's `**Status:**` to `open — gate failed`, create a `stuck` file with all three rounds and the remaining issues, and report. Do not start a fourth round.

## 6. Close the input

Follow `references/closing.md` for the input's type, then the journal entry. Then `references/prd.md`: stale PRD fragments, changes to `Goal`, `Core idea` or `Scenarios`.

## 7. Report

In the user's language, briefly:

- the plan's path and its milestones, one line each;
- the `Not defended against` list, for the user to accept before execution;
- the gate result (rounds, "scan clean, critic has no blocking notes", or what remains and the `stuck` file);
- new `question` files, each with its question in one line;
- the judge's `enough` lines, numbered;
- what moved to `loc/inbox/done/`, and what changed in `loc/PRD.md`.

End with the next step: `/masterskills:loc-orchestrate <NNN>` when the user decides. Do not start it.
