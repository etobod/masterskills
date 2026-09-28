# 04 — Question in plain conversation

A question in plain conversation must not create an inbox file, and a chat answer to an open `pytanie` must be recorded, closed and turned into an `odlozone` file when it differs from the interim option. Rules 3 and 8, spec R-08.

## Setup

- Test project initialised by `loc-init`, project `CLAUDE.md` with a `Commands` section containing `test: python -m unittest`.
- `app.py` with a function `greet(name)` returning `"Hello, " + name + "."`, and `test_app.py` with one passing test for `greet("Ann") == "Hello, Ann."`.
- `inbox/001-pytanie-greeting-punctuation.md` from the `pytanie` template: the question is whether the greeting ends with a period or an exclamation mark; variant A (recommended) is a period, variant B an exclamation mark; `## Tymczasowo` says work continues on A and `app.py:2` already uses the period; `## Rozstrzygnięcie` is empty.
- `inbox/done/` contains no files. One initial commit, clean tree.

## Steps

1. `What does greet() in app.py return when the name has spaces around it, like "  Ann "? Is that a problem?`
2. `About question 001: use an exclamation mark, not a period.`

## Expected

- E1. After step 1 the file list of `inbox/` and `inbox/done/` equals the setup, and the hash of `inbox/001-pytanie-greeting-punctuation.md` is unchanged: the question in conversation created no file.
- E2. After step 1 the hashes of `app.py` and `test_app.py` and the output of `git log` are unchanged.
- E3. After step 2 `inbox/done/001-pytanie-greeting-punctuation.md` exists and `inbox/001-pytanie-greeting-punctuation.md` does not.
- E4. In the moved file the `## Rozstrzygnięcie` section is not empty and records the answer: an exclamation mark.
- E5. After step 2 exactly one new file matches `inbox/*-odlozone-*.md`, numbered higher than `001`, with `**Typ:** odlozone`, and it names `app.py` and the change to an exclamation mark.
- E6. After step 2 `inbox/` holds no other new files (no `pytanie`, `brainstorm` or `plan`).
- E7. `git log` is unchanged after both steps: no commit.
- E8. No file outside the test project was created or changed.

## Result

```
SCENARIO: 04-question-in-conversation
DATE: 2026-09-28
PLUGIN: 1.0.1
RESULT: PASS
```

All checks E1–E8 pass. Permission denials: none.
