# 04 — Question in plain conversation

A question in plain conversation must not create an inbox file, and a chat answer to an open `question` must be recorded, closed and turned into a `deferred` file when it differs from the interim option. Rules 3 and 8, spec R-08.

## Setup

- Test project initialised by `loc-init`, project `CLAUDE.md` with a `Commands` section containing `test: python -m unittest`.
- `app.py` with a function `greet(name)` returning `"Hello, " + name + "."`, and `test_app.py` with one passing test for `greet("Ann") == "Hello, Ann."`.
- `loc/inbox/001-question-greeting-punctuation.md` from the `question` template: the question is whether the greeting ends with a period or an exclamation mark; variant A (recommended) is a period, variant B an exclamation mark; `## Interim` says work continues on A and `app.py:2` already uses the period; `## Resolution` is empty.
- `loc/inbox/done/` contains no files. One initial commit, clean tree.

## Steps

1. `What does greet() in app.py return when the name has spaces around it, like "  Ann "? Is that a problem?`
2. `About question 001: use an exclamation mark, not a period.`

## Expected

- E1. After step 1 the file list of `loc/inbox/` and `loc/inbox/done/` equals the setup, and the hash of `loc/inbox/001-question-greeting-punctuation.md` is unchanged: the question in conversation created no file.
- E2. After step 1 the hashes of `app.py` and `test_app.py` are unchanged.
- E3. After step 2 `loc/inbox/done/001-question-greeting-punctuation.md` exists and `loc/inbox/001-question-greeting-punctuation.md` does not.
- E4. In the moved file the `## Resolution` section is not empty and records the answer: an exclamation mark.
- E5. After step 2 exactly one new file matches `loc/inbox/*-deferred-*.md`, numbered higher than `001`, with `**Type:** deferred`, and it names `app.py` and the change to an exclamation mark.
- E6. After step 2 `loc/inbox/` holds no other new files (no `question`, `brainstorm` or `plan`).
- E7. No file outside the test project was created or changed.

## Result

```
SCENARIO: 04-question-in-conversation
DATE: 2026-09-28
PLUGIN: 1.2.0
RESULT: PASS
```

All checks pass. Permission denials: none.
