# 01 — Conversation becomes a plan

Loose talk about a feature must land in one growing `brainstorm` file, and a plan must come only from `loc-planning`, never straight from the conversation. Rules 7 (spec §6), F-02.

## Start

- Test project initialised by `loc-init`: `inbox/`, `inbox/done/`, `docs/`, project `CLAUDE.md` with a `Commands` section containing `test: python -m unittest`.
- One source file `app.py` with a function `greet(name)` returning `"Hello, " + name`, and `test_app.py` with one passing test.
- `inbox/` and `inbox/done/` contain no files. One initial commit, clean tree.

## Kroki

1. `Thinking about app.py — greet should support a language option, Polish and English. Not sure yet whether it should be a parameter or a config file.`
2. `A parameter is better, default English. And unknown languages should fall back to English, not crash.`
3. `loc-planning` on the brainstorm file, using its number: `loc-planning NNN` (take `NNN` from the file name created after step 1).

## Oczekiwane

- E1. After step 1 exactly one file matches `inbox/*-brainstorm-*.md`; its number `NNN` is three digits.
- E2. After step 2 there is still exactly one brainstorm file (the same `NNN`), and it contains decisions numbered `B-01`, `B-02`… covering "parameter, default English" and "unknown language falls back to English".
- E3. After steps 1–2 `app.py`, `test_app.py` and `git log` are unchanged: no code, no plan, no commit.
- E4. After step 3 exactly one file matches `inbox/*-plan-*.md`, numbered higher than the brainstorm.
- E5. The brainstorm file has moved to `inbox/done/` (same name) and is no longer in `inbox/`.
- E6. The plan has the sections: goal, what we do not do, context from code (at least one `app.py:<line>` reference), milestones, risks and decisions.
- E7. Every milestone has an automatic proof: a command and its expected result. The count of milestones equals the count of proofs.
- E8. The plan refers to the brainstorm decisions (`B-01`, `B-02`) and contains no open questions ("TBD", "TODO", "to be decided" or Polish "do ustalenia").
- E9. After step 3 `app.py` and `git log` are still unchanged: planning did not execute the plan and did not commit.
