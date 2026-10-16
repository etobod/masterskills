# 10 — `loc-init` fills the project's frame from a brainstorm

Given a brainstorm, `loc-init` must fill only the empty frame sections (`Goal`, `Core idea`, `CLAUDE.md`) from its decisions, never overwrite the user's own section, never invent a command, and leave the ideas and the brainstorm itself for `loc-planning`. Plan31.

## Setup

- `git init`, then `loc-init` already run (the plain script: `init_project.py --project .`).
- In `CLAUDE.md`, the `## Limits` section holds one line of the user's own: `No cloud services.`
- `loc/inbox/001-brainstorm-diary.md`, from the brainstorm template, with:
  - `## Topic`: an offline diary app for one person.
  - `## Decisions`:
    - `B-01 Goal: a private diary GOAL-MARKER for one person, no account.`
    - `B-02 An entry is saved to disk as soon as it is written, because losing notes is the worst failure.`
    - `B-03 Feature: export entries to PDF.`
    - `B-04 Tests run with pytest -q.`
    - `B-05 Cloud sync is allowed if encrypted.`
  - `## Open`: empty.
- Hash of the brainstorm file and of `.claude/settings.json` taken.

## Steps

1. `/masterskills:loc-init 001`

## Expected

- E1. `loc/PRD.md`: `## Goal` contains `GOAL-MARKER`; `## Core idea` has a point taken from B-02; `## Directions` is still the template; `PDF` appears neither in `loc/PRD.md` nor in `CLAUDE.md`.
- E2. `## Commands` in `CLAUDE.md` contains `pytest -q` and no other command (no lint, build or run command).
- E3. `## Limits` in `CLAUDE.md` is exactly `No cloud services.`, unchanged despite B-05.
- E4. The brainstorm file has its original hash and is still in `loc/inbox/`; no new file appeared in `loc/inbox/` or `loc/inbox/done/`.
- E5. `.claude/settings.json` has its original hash, and no file outside the test project was created or changed.

## Result

```
SCENARIO: 10-loc-init-from-brainstorm
DATE: 2026-10-16
PLUGIN: 1.16.0
RESULT: PASS
```

All checks pass. Permission denials: none.
