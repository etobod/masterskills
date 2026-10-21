---
name: loc-orchestrate
description: Use when the user asks to execute a plan from loc/inbox/ (e.g. "loc-orchestrate 018", "execute plan 018"), or to resume one that has a state file in loc/state/. Builds it milestone by milestone with a proof and a code-review per milestone, then a final review.
argument-hint: "<plan number or file>"
---

# loc-orchestrate

Executes `loc/inbox/NNN-plan-<topic>.md` milestone by milestone. The plan is the contract: build what it says, prove it with its `Proof` lines, review each milestone's diff, then the whole. Do not redesign it.

**Do not ask "shall I continue?" between milestones.**

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

## 1. Start

1. `$ARGUMENTS` is a plan number or file in `loc/inbox/`. No argument: if `loc/state/` holds a file whose `phase` is not `done`, resume it; otherwise the first plan in `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/plan_queue.py` (lowest group); no open plan: say so.
2. If `loc/state/<NNN>.json` exists, **resume** from its `next_action` (`references/state.md`).
3. Read the plan, the project's `CLAUDE.md` (`Commands`, `Invariants`, `Limits`) and `loc/PATTERNS.md`.
4. Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py --ready <plan>`. If it exits non-zero, the plan's status says the gate failed, or `loc/inbox/` has an open `PRD:` `question`, **stop**: say why, point to `/masterskills:loc-planning`.
5. Choose the mode: **inline** for one or two small milestones; **subagent** otherwise. Create the state file (`references/state.md`).
6. Copy the tests: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/test_baseline.py --plan <NNN>`.

## 2. Each milestone

Update the state file before and after every step.

1. **Snapshot** `--point start`.
2. **Implement** exactly this milestone, code and its tests together. With `**Criteria:**`: tests first, red gate `M<n>/red`, then the code (`references/tests.md`).
   - *inline*: do it yourself.
   - *subagent*: a fresh general-purpose sub-agent per milestone with the plan path, the milestone's heading and text, `Code context`, and the rules: only this milestone, follow the project's `CLAUDE.md`, scratch files only in `loc/tmp/` and delete only files you created there, never the directory, report the files changed and the proof output. The next steps check its report.
3. **Proof gate** (`M<n>/proof`). Increase `rounds`, run the `Proof` command exactly as written, compare with the expected result. Pass → next step. Fail → fix the cause (not the proof) and start the next round. After the third failed round: **stuck** (below).
4. **Snapshot** `--point end`. It prints the changed files.
5. **Code-review gate** (`M<n>/code-review`). Increase `rounds`, then `Skill(skill: "code-review", args: "<changed files> medium")`: always explicit files and level, **never `ultra`** (it leaves the machine). The `judge` agent weighs the Blocking and Non-blocking findings; fix those it marks `fix`. Suggestions, Unrealistic findings and its `enough` verdicts are not fixed: one line each in the plan's `## Review notes`. Rounds 2 and 3 review only the fixes (`references/gates.md`). Rerun the proof after the fixes and take a new `end` snapshot. Passed when the judge leaves nothing to fix. After the third failed round: **stuck**.
6. **Manual check**, only for `**Performer:** user (blocking)`, after the proof and the review passed: ask the user to do the milestone's `**Manual check:**`, exactly what to look at, and wait. For `user (deferrable)`, do not ask: append the `**Manual check:**` with the milestone and plan to an open `deferred` file of manual checks, or create one with the text in the same command (`next_number.py --type deferred … --what "<check, milestone, plan>" --why "user (deferrable)" --when "<when>"`). A fault the user reports first becomes a test that fails on it, then the fix, the proof and the review again; ask the user again only when that test passes. The user's word with the date goes under the milestone in the plan.
7. Mark the milestone `done`, move to the next one.

**Stuck gate.** No fourth round, no more code changes: add the gate to the plan's single `stuck` file (`references/stuck.md`), record it in the gate's `stuck`, set the milestone to `stuck`, and go on with the next milestone.

## 3. Deviations from the plan

- **Rules 1–3** (a bug, a missing critical piece such as validation, a blocker such as a missing dependency): fix it, record a deviation, carry on.
- A step of this skill you skipped (the red gate, the `test-author` agent, a review) is not a deviation: go back and do it; if it cannot be done, the gate is **stuck**.
- **Rule 4** (architecture: a new component, a changed interface or data model, a different library): create a `question` file with options, costs and a recommendation (`next_number.py --type question --by loc-orchestrate`), record the deviation with it, and continue on the recommendation.

## 4. When to stop

Only in these cases:

- **before the start**: step 1.4, or the file is not a plan;
- **expensive to undo**: data loss, a migration, anything outside the project, a rule 4 choice that cannot be reverted cheaply;
- **permissions**: a tool or access you do not have;
- **the end**.

A failed gate ends in `stuck`, not in a stop.

## 5. At the end

1. **QA gate** (`qa`), only when the plan has `**Criteria:**` (else report `**No tests:**`): `phase: qa`, `Skill(skill: "masterskills:loc-qa", args: "plan <NNN>")`. NOT APPROVED: fix the code behind each FAIL, never tests; next round. Third failure: **stuck**.
2. `phase: final-review`. `Skill(skill: "masterskills:loc-review", args: "plan <NNN>")` (orchestrated mode, gate `final-review`). Stuck: the architect's `triage` decides between more rounds, a `deferred` file and a question (`references/stuck.md`).
3. **Close what the plan resolved**: milestone `stuck` files whose points are all fixed now get `## Resolution` and move to `loc/inbox/done/` (`references/stuck.md`).
4. **Close the plan.** Under `## Resolution`: `done <date>`, one line per milestone (`M1 ✅`, or `M2 ⚠️ → loc/inbox/NNN-stuck-…`), deviations and new `question` files. `**Status:**` → `done <date>` and move it to `loc/inbox/done/` with `mv`; with a stuck `qa` gate → `open — QA failed`, not moved. Update `plan` in the state file, set `phase: journal`.
5. **Journal.** First, anything that failed during the plan and worked another way must be in `loc/PATTERNS.md` (rule 10): add what is missing. Then one command, your text (English, at most 3 sentences: what was done, what did not work out): `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type Plan --title "<title>" --text "<sentences> Details: <plan path>"`.
6. **Commit** the plan's files, never push: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/commit_plan.py --state loc/state/<NNN>.json --message "<type(scope): summary>"`, or `--skip "<reason>"` when the project's `CLAUDE.md` says the user commits. Rejected: report it, never bypass. Then `phase: done`, validate.
7. **Report** in the user's language, briefly: the commit, milestones with proof results, gates that went stuck, files closed in step 3, deviations, new inbox files, QA verdict, final review result. Then **"Judge: enough"**: every `enough` line, numbered in plan order, grouped by its PRD point; "fix 2" goes to `loc-planning`.
