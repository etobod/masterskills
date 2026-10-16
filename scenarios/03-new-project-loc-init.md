# 03 — New project through `loc-init`

`loc-init` must set up the full project structure in one run, never overwrite existing content and change nothing on a second run. Spec §3, `loc-init`, R-07.

## Setup

- Empty directory, `git init`, no commits.
- An existing `CLAUDE.md` with one line of the user's own: `Always answer in short sentences.`
- An existing `.gitignore` with one line: `*.log`.

## Steps

1. `loc-init`
2. `loc-init` again, after taking a snapshot of every file's hash in the project (excluding `.git/`).

## Expected

- E1. After step 1 these exist: `loc/inbox/`, `loc/inbox/done/`, `loc/PRD.md`, `loc/PATTERNS.md`, `loc/MEMORY.md`.
- E2. `CLAUDE.md` still contains `Always answer in short sentences.` unchanged, and now also has the headings `Commands`, `Invariants`, `Manual verification / UAT`, `Developer notes`, `Limits`.
- E3. `CLAUDE.md` has no project-goal section (the goal belongs in `loc/PRD.md`).
- E4. `.gitignore` still contains `*.log` and now also ignores `loc/`, in one line.
- E5. `loc/PRD.md`, `loc/PATTERNS.md` and `loc/MEMORY.md` are templates in English; `PATTERNS.md` has the three sections: works, does not work, pitfalls.
- E6. No file outside the test project was created or changed.
- E7. After step 2 every file hash matches the snapshot: the second run added nothing and overwrote nothing, and its reply says the project is already complete.
- E8. `.claude/settings.json` exists with `"autoMemoryEnabled": false` and an `attribution` object whose `commit` and `pr` are empty strings.
- E9. Variant without git: run step 1 in a directory without `git init`. `loc-init` says plainly that the project has no git and what will not work without it.

## Result

```
SCENARIO: 03-new-project-loc-init
DATE: 2026-09-28
PLUGIN: 1.2.0
RESULT: PASS
```

All checks pass. Permission denials: none.
