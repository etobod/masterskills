---
name: loc-init
description: Use when the user wants to set up masterskills in a project, or to bring an existing project up to date with the current plugin version (missing loc/ files, CLAUDE.md sections, the loc/ ignore entry or .claude/settings.json keys). Safe to run again.
argument-hint: "[project directory]"
---

# loc-init

Sets up the project structure. A script does all the work; you run it and report.

## Run

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/init_project.py --project "<dir>"
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

`<dir>` is `$ARGUMENTS` when given, otherwise `${CLAUDE_PROJECT_DIR}`. Run it exactly once. Do not create, edit or move any file yourself: the script decides what is missing and never overwrites anything.

## Report

The script prints JSON.

- **`ok: true`.** In one short list, tell the user:
  - what was **created** (`created`);
  - what was **added** to existing files (`updated`: file and the sections or entries added);
  - that everything else **already existed**;
  - each `skipped` file with its reason: the user fixes it by hand.
  `.claude/settings.json` turns off Claude's auto memory (lessons go to `loc/PATTERNS.md`) and AI attribution in commits and pull requests. If both `created` and `updated` are empty, say the project is already complete and nothing changed. Then point out the next step:
  - fill the empty `CLAUDE.md` sections (`Commands` first: skills run those commands and never guess them);
  - write the project's direction in `loc/PRD.md`.
- **`ok: false`.** Show `message` as it is, in the user's language, and stop. With `no-git` the directory is not the root of a git repository: plans snapshot milestones with git, reviews read the diff and work ends in a commit, so none of that works without it. Nothing was created. Do not run `git init` unless the user asks.

Do not commit the result; the user decides when.
