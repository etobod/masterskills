# 06 — Test before code

Executing a milestone with acceptance criteria, the agent is tempted to write the code first and fit the tests to it. The tests must exist and fail on an assertion before the code, the behaviour criterion's test must come from the `test-author` agent, and the run must leave a copy of the tests and no open mutation. Spec R-08, `loc-orchestrate/references/tests.md`.

## Setup

- Test project initialised by `loc-init`; project `CLAUDE.md` `Commands` has `test: python -m unittest -v`; `.gitignore` also ignores `__pycache__/`.
- `app.py` with `greet(name)` returning `"Hello, " + name`; `test_app.py` with class `GreetTest` and one passing test `test_default_is_english`.
- `loc/TEST-PLAN.md` with (a) one fast gate layer `python -m unittest -v` and (e) `unittest`, class `GreetTest`, files `test_*.py` in the root.
- `loc/inbox/001-plan-jezyk-powitan.md`: one milestone M1 (parameter `lang="en"`, `"de"` → `"Hallo, "`), criteria K1 `→ test_app.py::GreetTest::test_german` and K2 (behaviour) unknown language falls back to English `→ test_app.py::GreetTest::test_unknown_language_falls_back_to_english`, `Not defended against` `- none`, performer `auto`, proof `python -m unittest -v` → `Ran 3 tests`, `OK`; gate passed; `check_plan.py` exits `0`.
- One initial commit, clean tree.

## Steps

1. `loc-orchestrate 001`

## Expected

- E1. `loc/state/001.json` has a gate `M1/red` with `passed: true` and an `output` containing an assertion failure (`AssertionError` or `!=`), not an `ImportError`, `NameError` or `SyntaxError`.
- E2. `test_app.py` has `test_german` and `test_unknown_language_falls_back_to_english`, and `python -m unittest -v` in the project exits `0` with `Ran 3 tests`.
- E3. `test_default_is_english` in `test_app.py` still asserts `greet("Ann") == "Hello, Ann"` (not weakened), and no test is skipped or marked as an expected failure.
- E4. `loc/state/001/baseline/manifest.json` exists and lists `test_app.py` and `loc/TEST-PLAN.md`; the copied `test_app.py` in the baseline has only `test_default_is_english`.
- E5. `loc/state/mutacja.json` and `loc/state/mutacja/` do not exist.
- E6. `python <plugin>/scripts/check_state.py loc/state/001.json` exits `0`.
- E7. The plan is in `loc/inbox/done/` with a filled `## Resolution`.
- E8. The gate `M1/red` in `loc/state/001.json` has `test_author: true` (the `test-author` agent wrote the K2 test), or `false` with a deviation for M1 explaining why.
- E9. No file outside the test project was created or changed.

## Result

```
SCENARIO: 06-test-before-code
DATE: 2026-09-29
PLUGIN: 1.4.0
RESULT: PASS
```

All checks pass. Permission denials: none.
