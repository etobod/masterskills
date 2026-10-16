---
name: loc-orchestrate
description: Use when the user asks to execute a plan from loc/inbox/ (e.g. "loc-orchestrate 018", "execute plan 018"), or to resume one that has a state file in loc/state/. Builds it milestone by milestone with a proof and a code-review per milestone, then a final review.
argument-hint: "<plan number or file>"
---

# loc-orchestrate

Executes `loc/inbox/NNN-plan-<topic>.md` milestone by milestone. The plan is the contract: build what it says, prove it with its `Dowód` lines, review each milestone's diff, then the whole. Do not redesign it.

**Do not ask "shall I continue?" between milestones.**

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

## 1. Start

1. `$ARGUMENTS` is a plan number or file in `loc/inbox/`. No argument: if `loc/state/` holds a file whose `phase` is not `done`, resume it; otherwise, if `loc/inbox/` has exactly one plan, use it; else ask which.
2. If `loc/state/<NNN>.json` exists, **resume** from its `next_action` (`references/state.md`).
3. Read the plan, the project's `CLAUDE.md` (`Commands`, `Invariants`, `Limits`) and `loc/PATTERNS.md`.
4. Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py <plan>`. If it does not exit `0`, the plan's status says the gate did not pass, or `loc/inbox/` has an open `pytanie` titled `PRD:`, **stop**: say why and point to `/masterskills:loc-planning`.
5. Choose the mode: **inline** for one or two small milestones; **subagent** otherwise. Create the state file (`references/state.md`) and validate it.
6. Copy the tests: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/test_baseline.py --plan <NNN>`.

## 2. Each milestone

Update the state file before and after every step.

1. **Snapshot** `--point start`.
2. **Implement** exactly this milestone, code and its tests together. With `**Kryteria:**`: tests first, red gate `M<n>/red`, then the code (`references/tests.md`).
   - *inline*: do it yourself.
   - *subagent*: a fresh general-purpose sub-agent per milestone with the plan path, the milestone's heading and text, `Kontekst z kodu`, and the rules: only this milestone, follow the project's `CLAUDE.md`, scratch files only in `loc/tmp/` and delete only files you created there, never the directory, report the files changed and the proof output. The next steps check its report.
3. **Proof gate** (`M<n>/proof`). Increase `rounds`, run the `Dowód` command exactly as written, compare with the expected result. Pass → next step. Fail → fix the cause (not the proof) and start the next round. After the third failed round: **stuck** (below).
4. **Snapshot** `--point end`. It prints the changed files.
5. **Code-review gate** (`M<n>/code-review`). Increase `rounds`, then `Skill(skill: "code-review", args: "<changed files> medium")`: always explicit files and level, **never `ultra`** (it leaves the machine). The `judge` agent weighs the Blocking and Non-blocking findings; fix those it marks `fix`. Suggestions, Unrealistic findings and its `enough` verdicts are not fixed: one line each in the plan's `## Uwagi z przeglądów`. Rounds 2 and 3 review only the fixes (`references/gates.md`). Rerun the proof after the fixes and take a new `end` snapshot. Passed when the judge leaves nothing to fix. After the third failed round: **stuck**.
6. Mark the milestone `done`, move to the next one.

**Stuck gate.** No fourth round, no more code changes: add the gate to the plan's single `utknelo` file (`references/stuck.md`), record it in the gate's `stuck`, set the milestone to `stuck`, and go on with the next milestone.

## 3. Deviations from the plan

- **Rules 1–3** (a bug, a missing critical piece such as validation, a blocker such as a missing dependency): fix it, record a deviation, carry on.
- **Rule 4** (architecture: a new component, a changed interface or data model, a different library): create a `pytanie` file with options, costs and a recommendation (`next_number.py --type pytanie`), record the deviation with it, and continue on the recommendation. Stop only if that choice would be expensive to undo.

## 4. When to stop

Only in these cases, each in a few lines:

- **before the start**: the plan does not pass `check_plan`, is not a plan, or a `PRD:` `pytanie` is open;
- **expensive to undo**: data loss, a migration, anything outside the project, a rule 4 choice that cannot be reverted cheaply;
- **permissions**: a tool or access you do not have;
- **the end**.

A failed gate ends in `utknelo`, not in a stop.

## 5. At the end

1. **QA gate** (`qa`), only when the plan has `**Kryteria:**` (else report `**Bez testów:**`): `phase: qa`, `Skill(skill: "masterskills:loc-qa", args: "plan <NNN>")`. NOT APPROVED: fix the code behind each FAIL, never tests; next round. Third failure: **stuck**.
2. `phase: final-review`. `Skill(skill: "masterskills:loc-review", args: "plan <NNN>")` (orchestrated mode). It uses the state file's `final-review` gate.
3. **Close what the plan resolved**: milestone `utknelo` files whose points are all fixed now get `## Rozstrzygnięcie` and move to `loc/inbox/done/` (`references/stuck.md`).
4. **Close the plan.** Under `## Rozstrzygnięcie`: `wykonane <date>`, one line per milestone (`M1 ✅`, or `M2 ⚠️ → loc/inbox/NNN-utknelo-…`), deviations and new `pytanie` files. `**Status:**` → `wykonane <date>` and move it to `loc/inbox/done/` with `mv`; with a stuck `qa` gate → `otwarte — QA nie przeszło`, not moved. Update `plan` in the state file, set `phase: journal`, validate.
5. **Journal.** One command, your text (Polish, at most 3 sentences: what was done, what did not work out): `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type Plan --title "<title>" --text "<sentences> Szczegóły: <plan path>"`. Then `phase: done`, validate.
6. **Report** in the user's language, briefly: milestones with their proof results, gates that went stuck, files closed in step 3, deviations, new inbox files, QA verdict, final review result. Then **"Sędzia: dość"**: every `dość` line, numbered in plan order, grouped by its PRD point; "popraw 2" goes to `loc-planning`.
