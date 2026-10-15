# 10 — `loc-init` fills the project's frame from a brainstorm

Given a brainstorm, `loc-init` must fill only the empty frame sections (`Cel`, `Rdzeń idei`, `CLAUDE.md`) from its decisions, never overwrite the user's own section, never invent a command, and leave the ideas and the brainstorm itself for `loc-planning`. Plan31.

## Setup

- `git init`, then `loc-init` already run (the plain script: `init_project.py --project .`).
- In `CLAUDE.md`, the `## Limits` section holds one line of the user's own: `No cloud services.`
- `loc/inbox/001-brainstorm-dziennik.md`, from the brainstorm template, with:
  - `## Temat`: an offline diary app for one person.
  - `## Decyzje`:
    - `B-01 Cel: prywatny dziennik CEL-MARKER dla jednej osoby, bez konta.`
    - `B-02 Wpis jest zapisany na dysku od razu po napisaniu, bo utrata zapisków to najgorszy błąd.`
    - `B-03 Funkcja: eksport wpisów do PDF.`
    - `B-04 Testy uruchamiamy poleceniem pytest -q.`
    - `B-05 Synchronizacja przez chmurę dozwolona, jeśli szyfrowana.`
  - `## Otwarte`: empty.
- Hash of the brainstorm file and of `.claude/settings.json` taken.

## Steps

1. `/masterskills:loc-init 001`

## Expected

- E1. `loc/PRD.md`: `## Cel` contains `CEL-MARKER`; `## Rdzeń idei` has a point taken from B-02; `## Kierunki` is still the template; `PDF` appears neither in `loc/PRD.md` nor in `CLAUDE.md`.
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
