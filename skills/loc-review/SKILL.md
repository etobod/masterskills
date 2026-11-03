---
name: loc-review
description: Use when the user asks for a review of changes ("loc-review", "review what changed", "review plan 018"), and when loc-orchestrate finishes a plan. Runs the rubber-duck critic and code-review in parallel, checks the project's invariants. After a plan it fixes the findings; on its own it only reports, to loc/inbox/.
argument-hint: "[plan <NNN> | <git range> | <paths>] [low|medium|high|max]"
---

# loc-review

An independent look at a finished change: does it do what was asked, and is it correct? The reviewers get **the requirements and the change**, never the history of the session.

## 1. Mode, scope, requirements

Parse `$ARGUMENTS`:

- **Level**: `low`, `medium`, `high` or `max`; default `medium`. **`ultra` is recognised and dropped, never forwarded**: it sends the code to the cloud. Say so; use `medium`.
- **`plan <NNN>`, called by `loc-orchestrate`** → **orchestrated mode**. Requirements: the plan file. Scope: from `milestones[0].start` in `loc/state/<NNN>.json` to a fresh snapshot. Gate: `final-review` in that state file.
- **Anything else** → **standalone mode**, report only, no edits. Requirements: what the user named (a plan, an inbox file, their words); if nothing, "the change is correct and consistent with the project's rules". Scope: the git range given (`a..b`), else the named paths from `HEAD` (`--paths`), else everything uncommitted from `HEAD`.

Write the diff to a file and list the changed files (`loc/inbox/` is left out; without `--to` the end is a fresh snapshot):

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/review_diff.py --from <from> [--to <to>] --out loc/review/<NNN or date>.diff [--paths <paths>]
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

`empty: true` (only `loc/` changed): nothing to review; orchestrated, the gate gets `rounds: 0, passed: true`. Stop.

## 2. Review, in parallel

Start them in the same step, each once per round. An agent's empty answer is a lost report, never no findings: ask that same agent once for it, never a relaunch; still empty fails the round.

- **`rubber-duck` agent.** What was asked: the requirements (path or text). What was produced: the diff file and the changed files. Add: "Check the `Invariants` and `Limits` of `CLAUDE.md` and the `❌` entries of `loc/PATTERNS.md`."
- **`Skill(skill: "code-review", args: "<changed files> <level> — also flag new code the project, its standard library, platform or dependencies already provide")`**: always the explicit files and level (it otherwise reuses the last one). Orchestrated (milestones already reviewed), append "; review only how the milestones work together and what changed after the last milestone's `end`" with that snapshot hash.
- **Design review**, only when the project's `CLAUDE.md` has a filled `## Frontend` and a changed file is part of what the user sees: run the design review command named there on those files, read-only.

Meanwhile check yourself: every `Invariants` entry of the project's `CLAUDE.md` that the changed files touch, and every `❌` entry of `loc/PATTERNS.md` whose **When to use** matches them.

## 3. Merge

One list: duplicates merged, each finding with `file:line`, category (**Blocking**, **Non-blocking**, **Suggestion**, **Unrealistic** (`unrealistic`); code-review `high`, `medium`, `low`; definitions and the "who produces this?" test in `${CLAUDE_PLUGIN_ROOT}/skills/loc-orchestrate/references/gates.md`), the fix, and its source (`[rubber-duck]`, `[code-review]`, `[design]`, `[invariant]`). Check each against the code and give it a verdict (`gates.md`, "Verdicts"): a `rejected` one is dropped with one line saying why, a `needs_validation` one stays, marked unconfirmed. **"No findings" is a correct result**; do not invent any.

## 4. Orchestrated mode: fix, at most 3 rounds

Each round, in the state file's `final-review` gate: increase `rounds`, review (steps 1–3), give the Blocking and Non-blocking findings to the `judge` agent (`gates.md`, "The judge"), fix those it marks `fix`, rerun the `Proof` of every milestone the fixes touched. Suggestions, Unrealistic findings and the judge's `enough` verdicts are not fixed and create no inbox file: one line each in the plan's `## Review notes`, gate `final-review` (format in `gates.md`). A finding already there as `enough` goes to the judge marked as already judged and never gets a second line. The gate passes when the judge leaves nothing to fix; set `passed: true`.

After a third round (sixth, when the gate's `triage` holds `retry`) that still leaves something to fix: do not start another and change no more code. Write a `## final-review` section in the plan run's `stuck` file, creating it after round 3 (`${CLAUDE_PLUGIN_ROOT}/skills/loc-orchestrate/references/stuck.md`): each round's findings, what was changed, what remains with `file:line`, whether the rounds went in circles. Record it in the gate's `stuck`, and hand back to `loc-orchestrate`, whose architect decides what follows.

## 5. Standalone mode: report to inbox

With findings: create the file and fill `## Scope` (range, files, requirements) and `## Findings`, one line per finding in the merged format, the category first; an Unrealistic one with `Who produces it:` and the answer:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type review --slug "<scope>" --title "<what was reviewed>" --source "<range or plan>" --by loc-review
```

Fix nothing. The file has no `U`: `loc-planning` weighs it with the `judge` and plans each `fix`; only an architect escalation reaches the user. With no findings, or only Unrealistic ones, create no file; list them in the report.

## 6. Report

First, a command that failed and worked another way goes to `loc/PATTERNS.md` (rule 10).

Briefly, in the user's language: scope and level; findings by severity (or "no findings"); in orchestrated mode the rounds and what was fixed; the `review` or `stuck` file, if one was created.
