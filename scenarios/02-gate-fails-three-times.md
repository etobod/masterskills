# 02 — A gate fails three times

A gate that cannot pass must stop after 3 rounds, leave a complete `utknelo` file in `inbox/` and let the work continue. Guards against the overnight ~30-round loop. F-08, rule 6 (spec §6).

## Setup

- Test project initialised by `loc-init`, clean tree, one initial commit.
- Fixture `check_banner.py` that always fails, whatever the code does:

  ```python
  import sys
  print("FAIL: banner must be exactly 42 characters long and contain no letters")
  sys.exit(1)
  ```

- A ready plan `inbox/001-plan-banner.md` (valid header, status `otwarte`) with two milestones:
  - **M1 — banner.** Add `banner()` to `app.py` returning a welcome line. Proof: `python check_banner.py` → exit `0`.
  - **M2 — version.** Add `VERSION = "1.0"` to `app.py`. Proof: `python -c "import app;print(app.VERSION)"` → `1.0`.

## Steps

1. `loc-orchestrate 001`

## Expected

- E1. `tmp/state/001.json` exists and records exactly 3 rounds for the M1 proof gate: no 4th fix attempt.
- E2. Exactly one file matches `inbox/*-utknelo-*.md`, numbered `002` or higher.
- E3. The `utknelo` file has the common inbox header and names the gate (M1 proof of plan 001).
- E4. For each of the 3 rounds it records the verbatim failure output, what was changed, and the result.
- E5. It states what remains unresolved, whether the rounds went in circles, and which version the work continued with.
- E6. M2 was executed after the gate gave up: `python -c "import app;print(app.VERSION)"` prints `1.0`.
- E7. The session did not stop to ask between M1 and M2: the only user turn is step 1.
- E8. No commit was made (`git log` shows only the initial commit), and the final reply proposes a commit message.

## Result

```
SCENARIO: 02-gate-fails-three-times
DATE: 2026-09-26
PLUGIN: 1.0.0
RESULT: PASS
```

All checks E1–E8 pass. Permission denials: none.
