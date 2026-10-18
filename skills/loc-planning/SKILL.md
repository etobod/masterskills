---
name: loc-planning
description: Use when the user asks for a plan, or to turn a brainstorm, review, deferred item, stuck gate, answered question or PRD fragment into one (e.g. "loc-planning 004", "make a plan from the brainstorm"). Writes a plan with milestones and automatic proofs to loc/inbox/ and gates it. Never executes the plan.
argument-hint: "<inbox number or file | PRD fragment | task text>"
---

# loc-planning

Turns an input into `loc/inbox/NNN-plan-<group>-<difficulty>-<topic>.md`: a plan someone can execute without deciding anything.

**Do not execute the plan, do not change code.** Do the steps in order; none is optional.

## 1. Input

`$ARGUMENTS` is one of:

- **An inbox number or file**: `brainstorm`, `review`, `deferred`, `stuck`, or a `question` that already has an answer under `## Resolution`. The number is enough; find the file in `loc/inbox/`.
- **A fragment of `loc/PRD.md`**, named by its heading.
- **Plain text**: the task itself; `fix N`: the N-th `enough` line of the last report.

No argument: if `loc/inbox/` has exactly one `brainstorm`, use it; otherwise ask what to plan. An open `question` is not an input.

## 2. Read the code, not documents about it

1. The input, the project's `CLAUDE.md` (`Commands` gives the proof commands; `Invariants`, `Limits`, `Manual verification / UAT`) and `loc/PATTERNS.md` (entries whose **When to use** matches).
2. The code the change touches. For more than a couple of files, delegate to the `researcher` agent with the question "what exists today for <change>" and use its `file:line` report. Documents are not evidence; code is.
3. If the project has no `CLAUDE.md` `Commands` section, say so in the plan's risks and use the commands you verified by running them. A run leaves no files behind: nothing new in `git status --short` (Python: `python -B`).
4. Gaps in the frame: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/init_project.py --check` (writes nothing). Empty PRD sections: `references/prd.md`. Empty `CLAUDE.md` sections never stop you: what the plan can establish goes into a milestone, the rest into the report. Sections that contradict each other ("two separate chains" vs "one complex chain") become a `question` (step 4).

## 3. The judge decides which findings become work

**Required** when the input holds review findings: a `review`; a `stuck` section `## M<n> code-review` or `## final-review`; and every `deferred`, whatever it holds (review findings, observations from a manual check, or a `fix` deferred earlier: the PRD may have changed since). A `## plan gate` or `## qa` section of a `stuck` is planned as usual. Reviews of free-form input always find one more case; a plan that takes every leftover finding ends in the same stuck gates. The judge decides what is worth a plan, not the user and not you. Do not skip it because the plan's gate "will check": it checks only that you did this step. For a plan from a `review`, `check_plan.py` fails every finding that is neither in a milestone nor in `## Review notes`.

1. Number the findings: `<input NNN> #<n>`, in the order of the lines under the input's `## Findings` (`003 #1`, `003 #2`…). List each with `file:line` and category. Check each against the code as it is now; one already fixed gets one line under the input's `## Resolution` (`- 003 #4 already fixed: app.py:40`), never in the plan.
2. **Suggestions** (no change in behaviour: duplicated constants, docstrings, double parsing, dead code, speed) and **Unrealistic** findings (`${CLAUDE_PLUGIN_ROOT}/skills/loc-orchestrate/references/gates.md`) do not go to the judge and never into a milestone. Speed comes back only when the user reports that something is noticeably slow. An observation from a manual check has no category: it was seen in real use, so it is never a suggestion or unrealistic; it goes to the judge as Non-blocking, with the `file:line` it names, if any.
3. Call the `judge` agent with the Blocking and Non-blocking findings, the plan they came from (the input's `**Source:**`; none → `loc/PRD.md` and `Invariants` only), `loc/PRD.md` and `CLAUDE.md`. Wait for its verdicts. `fix` goes into a milestone, which cites the number (`Fixes 003 #1.`); `enough` does not. Never overrule a verdict, and never ask the user which findings to take: the report shows the `enough` ones, and the user may answer `fix N`.

Record every finding that is not in a milestone in the plan's `## Review notes` (before `## Resolution`), one line each, gate `planning`. Only these forms; `check_state.py` rejects anything else there:

```
- enough (planning): 003 #2 `parse.py:41` — "around five" gives an approximate 17:00. Reason: same part of day, the hour is marked approximate [Goal 2]
- suggestion (planning): 003 #3 `app.py:98` — the constant repeats the list from `text.py`
- unrealistic (planning): 003 #5 `app.py:240` — `force=False`. Who produces it: no caller in the code passes this value
- enough (planning): 014 #3 — the model added its own heading above the list. Reason: cosmetic, the list itself is correct [plan Goal]
```

The last form is an observation from a manual check: no `file:line` when it names none. `## Out of scope` gets: `Input findings without a fix verdict: ## Review notes.` In the plan's gate, a critic finding that repeats one of these lines goes to `## Risks and decisions` citing the verdict and is not blocking. Later reviews see the lines, so a finding judged here is not raised again without a new argument.

**No `fix` at all**: write no plan. Under the input's `## Resolution` write `→ no plan (<date>): the judge gave no fix`, then the lines; close the input (step 7, items 2–3). The journal entry points to `loc/inbox/done/<input>`. The report numbers the `enough` lines and ends without an orchestrate step.

**No `deferred` file** for any of these lines. A `deferred` is only for a `fix` finding deliberately left out of the plan, with the reason.

## 4. Unknowns become questions, not holes

Anything the user must decide goes to its own `question` file **before** the plan is written: first look for a similar open one and extend it; otherwise create one with the script (below) and fill it completely (context, options with cost, recommendation). The plan then proceeds on the recommendation and says so in `## Risks and decisions` (`→ loc/inbox/NNN-question-…`, interim option A). Stop without a plan only if that interim choice would be expensive to undo.

## 5. Write the plan

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type plan --slug "<group>-<difficulty>-<topic>" --title "<title>" --source "<input file or PRD heading or conversation>"
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

`<difficulty>` tells the user which model can run the plan: `easy` (each milestone a local change to existing code, no new file, interface or data model), `hard` (a new component, a changed interface or data model, or a risky change to code many callers rely on), otherwise `medium`. Milestone limit: `easy` 6, `medium` 4, `hard` 3, not counting an M1 that sets up the test suite. Never merge milestones to fit: work over the limit becomes several plans.

`<group>` is the plan's place in the queue of open plans (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/plan_queue.py`): a lower group runs first, and plans of one group change different files. Take the highest group in the queue when the plan changes no file its plans change, else that group + 1; an empty queue gives `1`. Urgent (the user says so): group `1`; when it shares files with a group `1` plan and must go first, run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/plan_queue.py --make-room 1 --keep <NNN>` after creating it. Several plans from one input: one that depends on another goes in a higher group; create them in queue order.

The file comes from the template with all sections. Fill them in English:

- **Goal**: what works afterwards, in terms the user can check.
- **Out of scope**: what is deliberately out of scope.
- **Not defended against**: who produces inputs the code deliberately does not defend against, with the reason (e.g. an administrator who could disable the tool anyway). Never a foreseeable user mistake. `- none` when nothing. Reviews call such inputs Unrealistic.
- **Code context**: the files and `file:line` the plan relies on, as read now.
- **Milestones**: `### M1 — <name>`, `### M2 …`. Each is a working, reviewable piece with exactly one `**Proof:**` line: a command and its expected result that **fails if the milestone is not done**. Optional `**Manual check:**` for what only a person can see (below). Code and its tests go in the same milestone (below). A milestone's product is never a decision, an audit or a question.
- **Risks and decisions**: references to brainstorm decisions (`B-01`…) and `question` files, and what each risk would cost.

### Tests in the plan

A milestone that changes only documents or configuration has no criteria: it says so with the reason, `**No tests:** documents only`. Every milestone that changes code has acceptance criteria. `check_plan.py` rejects a milestone with neither line.

What gets tested: the behaviour the plan changes (its criteria); regression (`loc-qa` runs the whole suite once at the end); fixed contracts (the project's `qa-*` skills, run by `loc-qa`); an explicit manual list from `Manual verification / UAT`.

A criterion says **what the code must do**, never "a test exists" or "it works":

```
**Criteria:**
- K1: `greet("Ann", "de")` returns `"Hallo, Ann"` → `test_app.py::test_german`
- K2 (behaviour): an unknown language gives the English greeting, no error → `test_app.py::test_unknown_language`
**Performer:** auto
**Proof:** `python -m unittest test_app` → `OK`
```

- Each criterion names its test in inline code: file and test name, or the id the framework runs directly (`test_app.TestGreet.test_german`). `loc-orchestrate` writes it **before** the code.
- The proof runs only this milestone's tests plus the fast layers of `loc/TEST-PLAN.md` (a), **never the full suite**: it runs in every round of its gate.
- `(behaviour)` marks behaviour seen from outside (a user-visible result, an error path, a contract), not an internal detail; a separate test author who has not seen the implementation writes those.
- A test may be weakened later only openly, with the reason in the execution report. Say so in `## Risks and decisions` when a criterion is likely to change.
- A criterion's test is never a shell check (`grep`, `test -f`, `open`): those prove a word or a file exists, not behaviour.
- A test runs the project's code, never its own copy of it: a copy passes whatever the code does. Code inside a page is tested by loading the page's `<script>` (Node: `readFileSync` and `vm`), not by pasting functions into the test.

**No test suite yet** (no test command in `CLAUDE.md` `Commands`, no `loc/TEST-PLAN.md`): the plan starts with **M1 — test suite**: the framework, the test directory and the command, added to `Commands`; one smoke test, proof: the command → `1 passed` (or the framework's equivalent); `loc/TEST-PLAN.md` copied from `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md` with sections (a) and (e) filled in. Write that path exactly so, never expanded: the plan must work on another machine. To see the template, read it at that path; do not search the disk. M1 needs no `**Criteria:**`. Planning writes only the plan and inbox files: never create `loc/TEST-PLAN.md` or a test to satisfy the gate. No obvious framework (one HTML page, a script, "zero dependencies"): keep the logic in pure functions and test them with the language's built-in runner (`node --test`, `python -m unittest`); what can only be seen gets a user performer.

`loc/TEST-PLAN.md` is the project's test contract and changes only through a milestone: when the plan adds something new to the product, one milestone extends section (b) (tests only).

**The user checks after your tests, never instead of them.** A user who finds the tenth bug a test could have caught stops trusting the plan. So every milestone that changes code has criteria with tests and a command proof, also when a person must look at the result; the user gets only what no command can see: the look, the feel, a real device, per `Manual verification / UAT`. Even a canvas animation has testable logic (the math, the data, the empty input), and that is tested first.

**Performer** (`**Performer:**`): `auto`, the proof command run by `loc-orchestrate` (default); `agent`, a check an agent performs and records; `user (blocking)` or `user (deferrable)`: after the proof and the code review pass, the user does the milestone's `**Manual check:**` and gives their word with a date. A user performer and a `**Manual check:**` line go together; a criterion may point to `manual` only next to criteria with tests:

```
**Criteria:**
- K1: `computeFourier([])` returns an empty list, no error → `tests/fourier.test.js::empty input`
- K2: the epicycles draw the shape smoothly → manual
**Performer:** user (deferrable)
**Manual check:** open `index.html`; the epicycles draw the shape smoothly
**Proof:** `node --test` → `pass 1`
```

Blocking stays in the plan; `loc-orchestrate` puts a deferrable check into a `deferred` file once the proof passes. There is no separate manual-test document.

Fixtures committed to git are written by hand. Data recorded from real runs goes only to a directory the project ignores, named in `loc/TEST-PLAN.md` (e).

## 6. Gate: at most 3 rounds

Each round, recorded as one line in `## Plan gate`:

1. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py <plan>` must exit `0`. Fix every issue it lists. An unaccounted review finding means step 3 was skipped: do it now, with the judge.
2. The `rubber-duck` agent with **what was asked** (the input file, or the PRD fragment or text) and **what was produced** (the plan path); ask it also whether a milestone does several independent things. Fix every Blocking and Non-blocking finding; a finding you reject goes into `## Risks and decisions` with the reason.

The round passes when the script exits `0` and the critic reports nothing blocking. After a failed third round: set the plan's `**Status:**` to `open — gate failed`, create a `stuck` file with all three rounds and the remaining issues, and report. Do not start a fourth round.

## 7. Close the input

Also after a plan that did not pass the gate, so the next attempt starts from the plan and the `stuck` file (whose `**Source:**` names the plan). Take the date with `date "+%Y-%m-%d"`; never from memory. Move files with `mv` (`loc/` is not in git). Nothing is ever deleted.

**Input file in `loc/inbox/`** (`brainstorm`, `review`, `deferred`, `stuck`, answered `question`):

1. Under `## Resolution` write `→ plan loc/inbox/NNN-plan-<topic>.md (<date>)`. Never rewrite the original content.
2. Set `**Status:**` to `closed <date>`.
3. Move it to `loc/inbox/done/` under the same name.
4. Point the plan's `**Source:**` to `loc/inbox/done/<name>`.

A `question` with an empty `## Resolution` is not closed: it stays open and the plan only refers to it. **A PRD fragment**: `references/prd.md`. **Plain text**: nothing to close; `**Source:**` says `conversation` with a one-line summary.

**Journal entry** (English, at most 3 sentences: what was planned, from which input, the gate result); no `loc/MEMORY.md`: skip it:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type Planning --title "<title>" --text "<sentences> Details: loc/inbox/NNN-plan-<topic>.md"
```

Then `references/prd.md` when a PRD fragment is stale, or the plan changes `Goal`, `Core idea` or `Scenarios`.

## 8. Report

In the user's language, briefly:

- the plan's path and its milestones, one line each;
- the `Not defended against` list, for the user to accept before execution;
- the gate result (rounds, "scan clean, critic has no blocking notes", or what remains and the `stuck` file);
- new `question` files, each with its question in one line;
- the judge's `enough` lines, numbered;
- what moved to `loc/inbox/done/`, and what changed in `loc/PRD.md`.

End with the next step: `/masterskills:loc-orchestrate <NNN>` when the user decides. Do not start it.
