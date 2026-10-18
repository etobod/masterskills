---
name: loc-init
description: Use when the user wants to set up masterskills in a project (optionally filling CLAUDE.md and the PRD's goal from a brainstorm, e.g. "loc-init 001"), or to bring an existing project up to date with the current plugin version (missing loc/ files, CLAUDE.md sections, the loc/ ignore entry or .claude/settings.json keys). Safe to run again.
argument-hint: "[project directory] [brainstorm number or file]"
---

# loc-init

Sets up the project structure. A script does all the work; you run it and report. Given a brainstorm, you then fill the empty sections that describe the project from it.

## Migrate first

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/migrate.py --project "<dir>"
```

It brings an existing `loc/` to the current format and prints JSON. When `from` equals `to` (or is null), nothing changed: go on. Otherwise it already renamed the files and translated every heading, field and marker; you translate the prose of each file in `translate` into English. Keep headings, fields, file names, `file:line`, code and quotes of the user's words as they are; change nothing but the language. Leave `question` files and `loc/inbox/done/` as they are. In `MEMORY.md` translate only the text above the index. Report the migration (`from` → `to`, renamed files, translated files) before the rest.

When `harvest` is true, the project has finished plans but no recorded decisions: call the `architect` agent in Harvest mode with `loc/PRD.md` and `CLAUDE.md`, and turn its report into one `question` file (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type question --slug "decisions" --title "Decision: record the project's decisions" --source "loc-init"`) with the candidates and the reversed choices, ending with the line `After the answer: write the approved lines to loc/PRD.md ## Decisions.` Nothing enters the PRD before the user approves.

`deferred` lists old plans that fail the plan check on their own text: they are now `deferred` items, to be planned again with `loc-planning`. When `regroup` is true, open plans have no group yet: call the `pm` agent to order the whole queue and run the `plan_queue.py --set` command it returns. Report both: each deferred plan with its reason, and the new queue order.

## Run

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/init_project.py --project "<dir>" --session "${CLAUDE_SESSION_ID}"
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

`$ARGUMENTS` may hold a project directory and a brainstorm, in any order:

- a directory → `<dir>`; none → `${CLAUDE_PROJECT_DIR}`;
- a number `NNN` → `loc/inbox/NNN-brainstorm-*.md` (or in `loc/inbox/done/`);
- a path to a `.md` file → that file.

Run each script exactly once (a brainstorm adds the read-only `--check`). Do not create, rename or move any file yourself: the scripts decide what is missing and never overwrite anything. The only exceptions are translating and the decisions `question` after a migration (above), and filling sections from a brainstorm (below).

## From a brainstorm

Only when a brainstorm was given and the script printed `ok: true`: follow `references/brainstorm.md`. A brainstorm number or file that does not exist: say so and stop after the report.

## Report

The script prints JSON.

- **`ok: true`.** In one short list, tell the user:
  - what was **created** (`created`); a new `claude.bat` resumes this session, `open-code.bat` updates the plugin and starts OpenCode;
  - what was **added** to existing files (`updated`: file and the sections or entries added);
  - that everything else **already existed**;
  - each `skipped` file with its reason: the user fixes it by hand.
  `.claude/settings.json` turns off Claude's auto memory (lessons go to `loc/PATTERNS.md`) and AI attribution in commits and pull requests. If both `created` and `updated` are empty, say the project is already complete and nothing changed. Then point out the next step:
  - fill the empty `CLAUDE.md` sections (`Commands` first: skills run those commands and never guess them);
  - write in `loc/PRD.md` what the project is for (`Goal`), the few points it stands on (`Core idea`), how it is used (`Scenarios`) and its ideas (`Directions`); the review judge weighs findings against the first three.
- **`ok: false`.** Show `message` as it is, in the user's language, and stop. With `no-git` the directory is not the root of a git repository: plans snapshot milestones with git, reviews read the diff and work ends in a commit, so none of that works without it. Nothing was created. Do not run `git init` unless the user asks.

