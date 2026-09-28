# 07 — Unknown `qa-paths:` field in a project skill

A project has its own QA skills. One declares `qa-paths:`, a header field Claude Code does not know; the other does not. `loc-qa` must load and run the first because a changed file matches its paths, and must list the second as available but not run, instead of running everything or nothing. Spec R-08, `loc-qa` step 5.

## Setup

- Test project initialised by `loc-init`; project `CLAUDE.md` `Commands` has `test: python -m unittest discover -s tests -v`; `.gitignore` also ignores `__pycache__/`. No `loc/TEST-PLAN.md`, no plan, no state file.
- `src/api/users.py` with `user_name(user)`, `src/ui/page.py` with `title(text)`, and passing tests `tests/test_api_users.py` and `tests/test_ui_page.py`.
- `.claude/skills/qa-api/SKILL.md` with `qa-paths: ["src/api/**"]` in its header; its steps run the API tests and write `loc/state/qa-api-ran.txt` with the `Ran N tests` line.
- `.claude/skills/qa-docs/SKILL.md` without `qa-paths:`.
- One initial commit, then uncommitted changes in `src/api/users.py` and `src/ui/page.py` (both tests still pass).

## Steps

1. `loc-qa`

## Expected

- E1. A QA file `loc/state/qa-<YYYY-MM-DD>.md` exists with a `**Werdykt:**` line.
- E2. `loc/state/qa-api-ran.txt` exists and contains `Ran 1 test`: the `qa-api` skill was loaded and its steps were run.
- E3. The QA file has a row for `qa-api` with status `PASS`.
- E4. The QA file has a row for `qa-docs` with status `INFO` saying it is available and was not run (`dostępny, nie uruchomiony` or equivalent), and the file or the session reply mentions adding `qa-paths:` to run it automatically.
- E5. `src/api/users.py` and `src/ui/page.py` equal their state after setup (hash), and `git log` equals the setup (no commit).
- E6. No file outside the test project was created or changed.

## Result

```
SCENARIO: 07-qa-paths-field
DATE: 2026-09-28
PLUGIN: 1.2.0
RESULT: PASS
```

All checks pass. Permission denials: none.
