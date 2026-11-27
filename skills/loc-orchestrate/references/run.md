# Running a plan

The procedure of the `orchestrator` agent. `loc-orchestrate` has checked the frame and the plan, created the state file and copied the tests; you get the plan's path and its state file. The plan is the contract: build it, prove each milestone with its `Proof` lines and a quick code review, then review the whole plan. Do not redesign it.

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it. **Never ask the user anything and never ask "shall I continue?"**: what needs the user goes into the state file's `questions` (below).

**Long commands.** Every proof, test run and metric, in any step or reference (search, divergent, a rerun after a fix, QA), runs in the foreground with the command tool's timeout at its maximum, `600000` ms; never start one while another still runs. A foreground run the timeout kills is no failure: run it again in the background, as below, never with `&` or a detached start: wait for it at most three times 10 minutes, a wait that ends when the command ends, killed included, never an endless `until` loop. Still running after that: stop it and count the round as failed, cause `exceeds the time limit`, never a code fix. Before a milestone becomes `done` or `stuck`, before the final review, the QA gate and every stop or report, stop every background command you started that still runs.

## 1. Resume

Read the state file (`references/state.md`) and continue from its `next_action`: never repeat a recorded step or reset a round counter. Read the plan, the project's `CLAUDE.md` (`Commands`, `Invariants`, `Limits`) and `loc/PATTERNS.md`. Answers the user gave since your last run are under `## Resolution` of the files in `loc/inbox/done/` and in the plan; follow them.

## 2. Each milestone

Update the state file before and after every step.

A milestone with `**Kind:** search` runs the search loop of `references/search.md` instead of steps 2 and 3; a missed target is its accepted result, never stuck. A milestone with `**Kind:** divergent` follows `references/divergent.md` instead of steps 2 and 3: variants, the critic, an interim pick; its proof's `waiting: user pick` is done, never stuck. A milestone that changes what the user sees, and the plan's end, follow `references/design.md` (the `designer` agent, `ui_check.py`, the `design-critic` gate).

1. **Snapshot** `--point start`.
2. **Implement** exactly this milestone yourself, code and its tests together. With `**Criteria:**`: tests first, red gate `M<n>/red`, then the code (`references/tests.md`). Before writing code, climb the ladder and stop at the first rung that works: is it needed at all, already in the project, in the standard library, a platform feature (the browser's date picker), an installed dependency, one line; only then the minimum that works. Never cut validation, error handling, security or accessibility. Scratch files only in `loc/tmp/`; delete only files you created there, never the directory.
3. **Proof gate** (`M<n>/proof`). Increase `rounds`, run each `Proof` line exactly as written, one at a time, and compare each with its expected result. Run it as **Long commands** above says. Pass → next step. Fail → fix the cause (not the proof) and start the next round. After the third failed round: **stuck** (below).
4. **Snapshot** `--point end`. It prints the changed files.
5. **Quick code-review gate** (`M<n>/code-review`, `phase: code-review`; `references/gates.md`, "The milestone gate"): code-review `low` on the changed files, only Blocking findings fixed, the judge only when there is one, no rubber-duck; Non-blocking findings and the Blocking ones the judge called `enough` wait in the gate's `pending` for the final review. Only when the state file has `"review": "milestone"`; a state file without it (a run before 2.32) skips it.
6. **Manual check**, only for a `user` performer, after the proof passed: put the milestone's `**Manual check:**` on the checks sheet, `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/checks.py --add --plan <NNN> --milestone M<n> --title "<what>" --step "<what to open or click>" --look "<what to look at>"` (`--image "<png> | <caption>"` per screenshot; `--blocking` for `user (blocking)`). Blocking: add the sheet to `questions` and stop with `waiting: questions`; deferrable: go on. A rating the user gave (`checks.py --rate`) with a `fix` first becomes a test that fails on it, then the fix, the proof and step 5 again, then a new point with `--again <n>`. The answer with the date goes under the milestone in the plan.
7. Stop your background commands (**Long commands**), mark the milestone `done`, move to the next one.

**Stuck gate.** No fourth round or code change: stop your background commands (**Long commands**), record the gate in the plan's `## Stuck gates` (`references/stuck.md`), set its `stuck` to `"plan"` and the milestone to `stuck`, and go on with the next milestone.

## 3. Deviations from the plan

- **Rules 1–3** (a bug, a missing critical piece like validation, a blocker like a missing dependency): fix it, record a deviation, carry on.
- **A blocker only the user can remove** (a file outside the project is gone): a `question` file at once, added to `questions`; the milestone `stuck`, then the next one.
- A step of this procedure you skipped (the red gate, the `test-author` agent, a proof) is not a deviation: go back and do it; if it cannot be done, the gate is **stuck**.
- **Rule 4** (architecture: a new component, a changed interface or data model, a different library): call the `architect` agent in Decide mode with options, costs and your recommendation; record the deviation with its ruling, or, when it escalates, with its options as a `### <choice>` in the plan's one `question` file (the first creates it: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type question --title "Plan <NNN>: questions" --source "<plan path>" --by "architect (Decide)"`, then add it to `questions`), and continue on the recommendation.

## 4. Questions and when to stop

`questions` in the state file lists what waits for the user, each `{"file": "<the question file or the checks sheet>", "ask": "<one line>"}`. `loc-orchestrate` asks them in one round, records the answers, empties the list and starts you again.

Stop, with the report below, only in these cases:

- **waiting: questions**: a blocking manual check, or a matter whose recommended option is expensive to undo (data loss, a migration, anything outside the project, a rule 4 choice that cannot be reverted cheaply);
- **stopped: permissions**: a tool or access you do not have;
- **done**: the end.

A failed gate ends in `stuck`, not in a stop. Before stopping, `next_action` says what follows the answers.

## 5. At the end

1. `phase: final-review`. `Skill(skill: "masterskills:loc-review", args: "plan <NNN>")` (orchestrated mode, gate `final-review`). It comes first: its fixes are the last code changes, and the full suite must run after them. A stuck final review goes to the architect's triage (`references/stuck.md`) at once, so a `retry` also comes before QA. Tests `loc-qa` writes are judged by the next whole-suite review.
2. **QA gate** (`qa`), only when the plan has `**Criteria:**` (else report `**No tests:**`): `phase: qa`, `Skill(skill: "masterskills:loc-qa", args: "plan <NNN>")`. NOT APPROVED: fix the code behind each FAIL, never tests (a small fix with no review of its own); next round. Third failure: **stuck**. Then, when QA reported `suite review due`, `Skill(skill: "masterskills:loc-review", args: "tests")`: its review file is planned like any other.
3. **Close what the plan resolved**, then **triage** (`references/stuck.md`): mark the fixed points of `## Stuck gates`; a point still open, a stuck `qa` included, goes to the architect, whose `triage` decides between a `deferred` file and a question; no `retry` now, it would change code after QA.
4. **Close the plan.** Under `## Resolution`: `done <date>`, one line per milestone (`M1 ✅`, or `M2 ⚠️ → loc/inbox/NNN-deferred-…`), deviations and new `question` files. `**Status:**` → `done <date>` and move it to `loc/inbox/done/` with `mv`; with a stuck `qa` gate → `open — QA failed`, not moved. Update `plan` in the state file, set `phase: journal`.
5. **Journal.** First, add to `loc/PATTERNS.md` what failed during the plan and worked another way (rule 10). Then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/plan_cost.py --state loc/state/<NNN>.json` and one command, your text (English, at most 3 sentences: what was done, what did not work out): `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type Plan --title "<title>" --text "<sentences> Cost: <its line>. Details: <plan path>"`. Then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/diagram_needed.py --state loc/state/<NNN>.json`, and `Skill(skill: "masterskills:loc-diagram", args: "overview")` only when it prints `"needed": true`.
6. **Commit** the plan's files, never push: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/commit_plan.py --state loc/state/<NNN>.json --message "<type(scope): summary>"`, or `--skip "<reason>"` when the project's `CLAUDE.md` says the user commits. A new directory git tracks nothing in stops it: run again with `--add <dir>` for the plan's own work or `--leave <dir>` for files it did not make (e.g. manual-check data), then a `question` file (added to `questions`) asks whether `<dir>` goes into `.gitignore`. Rejected: report it, never bypass. Then `phase: done`.

## 6. Report

Always this shape, in English:

```
Status: done | waiting: questions | stopped: permissions — <what is missing>
<the report>
End of report.
```

The report, briefly: the commit, milestones with proof results, gates that went stuck, files closed in step 3 of §5, deviations, new inbox files, the checks sheet with its open points, QA verdict, final review result, the cost line. Then **Judge: enough**: every `enough` line, numbered in plan order, grouped by its PRD point. Waiting: what you need and what you do after the answers.
