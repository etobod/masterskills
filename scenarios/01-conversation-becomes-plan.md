# 01 — Conversation becomes a plan

Loose talk about a feature must land in one growing `brainstorm` file, and a plan must come only from `loc-planning`, never straight from the conversation. Rules 7 (spec §6), F-02.

## Setup

- Test project initialised by `loc-init`: `loc/inbox/`, `loc/inbox/done/`, `loc/PRD.md`, `loc/PATTERNS.md`, `loc/MEMORY.md`, project `CLAUDE.md` with a `Commands` section containing `test: python -m unittest`.
- One source file `app.py` with a function `greet(name)` returning `"Hello, " + name`, and `test_app.py` with one passing test.
- `loc/inbox/` and `loc/inbox/done/` contain no files. One initial commit, clean tree.

## Steps

1. `Thinking about app.py — greet should support a language option, Polish and English. Not sure yet whether it should be a parameter or a config file.`
2. `A parameter is better, default English. And unknown languages should fall back to English, not crash.`
3. `loc-planning` on the brainstorm file, using its number: `loc-planning NNN` (take `NNN` from the file name created after step 1).

## Expected

- E1. After step 1 exactly one file matches `loc/inbox/*-brainstorm-*.md`; its number `NNN` is three digits.
- E2. After step 2 there is still exactly one brainstorm file (the same `NNN`), and it contains decisions numbered `B-01`, `B-02`… covering "parameter, default English" and "unknown language falls back to English".
- E3. After steps 1–2 `app.py`, `test_app.py` and `git log` are unchanged: no code, no plan, no commit.
- E4. After step 3 exactly one file matches `loc/inbox/*-plan-*.md`, numbered higher than the brainstorm.
- E5. The brainstorm file has moved to `loc/inbox/done/` (same name) and is no longer in `loc/inbox/`.
- E6. The plan has the sections: goal, what we do not do, context from code (at least one `app.py:<line>` reference), milestones, risks and decisions.
- E7. Every milestone has an automatic proof: a command and its expected result. The count of milestones equals the count of proofs.
- E8. The plan refers to the brainstorm decisions (`B-01`, `B-02`) and contains no open questions ("TBD", "TODO", "to be decided" or Polish "do ustalenia").
- E9. After step 3 `app.py` and `git log` are still unchanged and `git status --short` is empty: planning did not execute the plan, did not commit and left no files behind (such as `__pycache__/`).

## Result

```
SCENARIO: 01-conversation-becomes-plan
DATE: 2026-09-28
PLUGIN: 1.3.0
RESULT: PASS
```

All checks pass. Run from the plugin installed from GitHub (`/plugin marketplace add etobod/masterskills`, `--plugin-dir` set to the install path). Permission denials: none.
