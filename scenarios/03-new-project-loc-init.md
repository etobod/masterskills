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

- E1. After step 1 these exist: `inbox/`, `inbox/done/`, `docs/PRD.md`, `docs/PATTERNS.md`, `docs/MEMORY.md`.
- E2. `CLAUDE.md` still contains `Always answer in short sentences.` unchanged, and now also has the headings `Commands`, `Invariants`, `Manual verification / UAT`, `Developer notes`, `Limits`.
- E3. `CLAUDE.md` has no project-goal section (the goal belongs in `docs/PRD.md`).
- E4. `.gitignore` still contains `*.log` and now also ignores `tmp/`.
- E5. `docs/PRD.md`, `docs/PATTERNS.md` and `docs/MEMORY.md` are templates in Polish; `PATTERNS.md` has the three sections: works, does not work, pitfalls.
- E6. No file outside the test project was created or changed.
- E7. After step 2 every file hash matches the snapshot: the second run added nothing and overwrote nothing, and its reply says the project is already complete.
- E8. `.claude/settings.json` exists with `"autoMemoryEnabled": false` and an `attribution` object whose `commit` and `pr` are empty strings.
- E9. Variant without git: run step 1 in a directory without `git init`. `loc-init` says plainly that the project has no git and what will not work without it.

## Result

```
SCENARIO: 03-new-project-loc-init
DATE: 2026-09-26
PLUGIN: 1.0.0
RESULT: PASS
```

All checks E1–E9 pass. Permission denials: none.
