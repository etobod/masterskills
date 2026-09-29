---
name: loc-review
description: Use when the user asks for a review of changes ("loc-review", "review what changed", "review plan 018"), and when loc-orchestrate finishes a plan. Runs the rubber-duck critic and code-review in parallel, checks the project's invariants. After a plan it fixes the findings; on its own it only reports, to loc/inbox/.
argument-hint: "[plan <NNN> | <git range> | <paths>] [low|medium|high|max]"
---

# loc-review

An independent look at a finished change: does it do what was asked, and is it correct? The reviewers get **the requirements and the change**, never the history of the session.

## 1. Mode, scope, requirements

Parse `$ARGUMENTS`:

- **Level**: `low`, `medium`, `high` or `max`; default `medium`. **`ultra` is recognised and dropped, never forwarded**: it sends the code to the cloud. Say so in one line and use `medium`.
- **`plan <NNN>`, called by `loc-orchestrate`** → **orchestrated mode**. Requirements: the plan file. Scope: from `milestones[0].start` in `loc/state/<NNN>.json` to a fresh snapshot. Gate: `final-review` in that state file.
- **Anything else** → **standalone mode**, report only, no edits. Requirements: what the user named (a plan, an inbox file, their words); if nothing, "the change is correct and consistent with the project's rules". Scope: the git range given (`a..b`), else the named paths from `HEAD` (`--paths`), else everything uncommitted from `HEAD`.

Write the diff to a file and list the changed files (`loc/inbox/` is left out; without `--to` the end is a fresh snapshot):

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/review_diff.py --from <from> [--to <to>] --out loc/review/<NNN or date>.diff [--paths <paths>]
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

`empty: true`: say there is nothing to review, and stop.

## 2. Review, in parallel

Start both in the same step:

- **`rubber-duck` agent.** What was asked: the requirements (path or text). What was produced: the diff file and the changed files. Add: "Check the `Invariants` and `Limits` of `CLAUDE.md` and the `❌` entries of `loc/PATTERNS.md`."
- **`Skill(skill: "code-review", args: "<changed files> <level>")`**: always the explicit files and level, because `code-review` otherwise reuses the level typed last.

Meanwhile check yourself: every `Invariants` entry of the project's `CLAUDE.md` that the changed files touch, and every `❌` entry of `loc/PATTERNS.md` whose **Kiedy stosować** matches them.

## 3. Merge

One list: duplicates merged, each finding with `file:line`, category (**Blocking**, **Non-blocking**, **Suggestion**, **Unrealistic** (`nierealna`); code-review `high`, `medium`, `low`; definitions and the "who produces this?" test in `${CLAUDE_PLUGIN_ROOT}/skills/loc-orchestrate/references/gates.md`), the fix, and its source (`[rubber-duck]`, `[code-review]`, `[invariant]`). Check each against the code before accepting it; a finding the code does not support is dropped, with one line saying why. **"No findings" is a correct result**; do not invent any.

## 4. Orchestrated mode: fix, at most 3 rounds

Each round, in the state file's `final-review` gate: increase `rounds`, review (steps 1–3), fix the Blocking and Non-blocking findings, rerun the `Dowód` of every milestone the fixes touched. Suggestions and Unrealistic findings are not fixed and create no inbox file: one line each in the plan's `## Uwagi z przeglądów`, gate `final-review` (format in `gates.md`). A finding you reject goes into the report with the reason. The gate passes when a round has no Blocking or Non-blocking finding; set `passed: true`.

After a third round that still has Blocking or Non-blocking findings: do not start a fourth and change no more code. Create a `utknelo` file (`next_number.py --type utknelo`, source: the plan) with its `**Kategoria:**`, each round's findings, what was changed, what remains with `file:line`, and whether the rounds went in circles. Record it in the gate's `stuck`, and hand back to `loc-orchestrate`, which closes the plan anyway.

## 5. Standalone mode: report to inbox

With findings: create the file and fill `## Zakres` (range, files, requirements) and `## Uwagi`, one line per finding in the merged format, the category first; an Unrealistic one with `Kto to wytwarza:` and the answer:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type przeglad --slug "<scope>" --title "<what was reviewed>" --source "<range or plan>"
```

Do not fix anything: the user decides, and `loc-planning` can turn the review into a plan. With no findings, or only Unrealistic ones, create no file: nothing waits for the user; list them in the report.

## 6. Report

In the user's language, briefly: scope and level; findings by severity (or "brak uwag"); in orchestrated mode the rounds and what was fixed; the `przeglad` or `utknelo` file, if one was created.
