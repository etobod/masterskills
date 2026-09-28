---
name: loc-orchestrate
description: Use when the user asks to execute a plan from loc/inbox/ (e.g. "loc-orchestrate 018", "execute plan 018"), or to resume one that has a state file in loc/state/. Builds it milestone by milestone with a proof and a code-review per milestone, then a final review. Never commits.
argument-hint: "<plan number or file>"
---

# loc-orchestrate

Executes `loc/inbox/NNN-plan-<topic>.md` milestone by milestone. The plan is the contract: build what it says, prove it with its `Dowód` lines, review each milestone's diff, then the whole. Do not redesign it.

**Do not commit or push. Do not ask "shall I continue?" between milestones.**

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

## 1. Start

1. `$ARGUMENTS` is a plan number or file; find it in `loc/inbox/`. No argument: if `loc/state/` holds a file whose `phase` is not `done`, resume it; otherwise, if `loc/inbox/` has exactly one plan, use it; else ask which.
2. If `loc/state/<NNN>.json` exists, **resume** from its `next_action` (`references/state.md`).
3. Read the plan, the project's `CLAUDE.md` (`Commands`, `Invariants`, `Limits`) and `loc/PATTERNS.md`.
4. Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py <plan>`. If it does not exit `0`, or the plan's status says the gate did not pass, **stop**: say why and point to `/masterskills:loc-planning`.
5. Choose the mode: **inline** for one or two small milestones; **subagent** otherwise. Create the state file (`references/state.md`) and validate it.

## 2. Each milestone

Update the state file before and after every step.

1. **Snapshot** `--point start`.
2. **Implement** exactly this milestone, code and its tests together.
   - *inline*: do it yourself.
   - *subagent*: a fresh general-purpose sub-agent per milestone with the plan path, the milestone's heading and text, `Kontekst z kodu`, and the rules: only this milestone, no commits, follow the project's `CLAUDE.md`, report the files changed and the proof output. The next steps check its report.
3. **Proof gate** (`M<n>/proof`). Increase `rounds`, run the `Dowód` command exactly as written, compare with the expected result. Pass → next step. Fail → fix the cause (not the proof) and start the next round. After the third failed round: **stuck** (below).
4. **Snapshot** `--point end`. It prints the changed files.
5. **Code-review gate** (`M<n>/code-review`). Increase `rounds`, then `Skill(skill: "code-review", args: "<changed files> medium")`: always explicit files and level, **never `ultra`** (it leaves the machine). Fix every finding; rerun the proof after the fixes and take a new `end` snapshot. A finding you reject after checking it goes into the final report with the reason. Passed when a round has nothing left to fix. After the third failed round: **stuck**.
6. Mark the milestone `done`, move to the next one.

**Stuck gate.** Do not start a fourth round. Create the file:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type utknelo --slug "<plan topic> m<n> <gate>" --title "<plan> — M<n>, <gate>" --source "<plan path>"
```

Fill every section: the gate and milestone; per round the verbatim failure output, what you changed and the result; what remains with `file:line`; whether the rounds went in circles; and which version of the code the work continued with. Record its path in the gate's `stuck`, set the milestone to `stuck`, and go on with the next milestone.

## 3. Deviations from the plan

- **Rules 1–3** (a bug, a missing critical piece such as validation, a blocker such as a missing dependency): fix it, record a deviation, carry on.
- **Rule 4** (architecture: a new component, a changed interface or data model, a different library): create a `pytanie` file with options, costs and a recommendation (`next_number.py --type pytanie`), record the deviation with it, and continue on the recommendation. Stop only if that choice would be expensive to undo.

## 4. When to stop

Only in these cases, each in a few lines:

- **before the start**: the plan does not pass `check_plan`, or it is not a plan;
- **expensive to undo**: data loss, a migration, anything outside the project, a rule 4 choice that cannot be reverted cheaply;
- **permissions**: a tool or access you do not have;
- **the end**.

A failed gate ends in `utknelo`, not in a stop.

## 5. At the end

1. `phase: final-review`. `Skill(skill: "masterskills:loc-review", args: "plan <NNN>")` (orchestrated mode). It uses the state file's `final-review` gate.
2. **Close the plan.** Under `## Rozstrzygnięcie`: `wykonane <date>`, one line per milestone (`M1 ✅`, or `M2 ⚠️ → loc/inbox/NNN-utknelo-…`), deviations and new `pytanie` files. `**Status:**` → `wykonane <date>`. Move it to `loc/inbox/done/` with `mv`. Update `plan` in the state file, set `phase: journal`, validate.
3. **Journal.** `Skill(skill: "masterskills:loc-journal", args: "loc/inbox/done/<plan file>")`, then `phase: done`, validate.
4. **Report** in the user's language, briefly: milestones with their proof results, gates that went stuck, deviations, new inbox files, final review result. Then a **proposed commit message** (Conventional Commits, English, no mention of AI and no `Co-authored-by`) and the sentence that you commit only when asked.
