# The state file `loc/state/<NNN>.json`

`<NNN>` is the plan's number. The file is the memory of the run: after `/clear`, compaction or a new session, the next step is read from it, never guessed or asked. Write it in English, with the Write or Edit tool (a script or heredoc asks for permission). Update it **before** each step starts and **after** each step ends, then validate:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_state.py loc/state/<NNN>.json
```

Exit `0` or fix the file and run it again. Take the time from `date "+%Y-%m-%d %H:%M"`.

## Start value

One entry in `milestones` per `### ` heading under `## Kamienie milowe`, in order:

```json
{
  "plan": "loc/inbox/018-plan-csv-export.md",
  "mode": "inline",
  "milestone": 1,
  "phase": "start",
  "milestones": [
    {"id": "M1", "status": "pending", "start": null, "end": null},
    {"id": "M2", "status": "pending", "start": null, "end": null}
  ],
  "gates": {},
  "deviations": [],
  "next_action": "Take the start snapshot of M1, then implement M1: <one line>",
  "updated": "2026-01-15 14:30"
}
```

## Fields

- `mode`: `inline` or `subagent`. When you switch mid-run, change it and add a deviation (rule 3) saying why.
- `milestone`, `phase`: where the run is. Phases in order: `start`, then per milestone `implement` → `proof` → `code-review`, then `qa` (plans with `**Kryteria:**`), `final-review`, `journal`, `done`.
- `milestones[].status`: `pending`, `in_progress`, `done` (proof passed, review passed) or `stuck` (a gate gave up; the run went on). `start` and `end` are snapshot hashes, written only by the snapshot script:

  ```sh
  sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/snapshot.py --state loc/state/<NNN>.json --milestone <n> --point start
  sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/snapshot.py --state loc/state/<NNN>.json --milestone <n> --point end
  ```

  `--point end` prints the milestone's `diff` command and changed `files`. Take a new `end` after every fix, so the diff always matches the tree.
- `gates`: one entry per gate that ran: `M<n>/red` (`references/tests.md`), `M<n>/proof`, `M<n>/code-review`, `qa`, `final-review`. Each is `{"rounds": <n>, "passed": <bool>, "stuck": null}`; a `M<n>/code-review` in round 2 or 3 keeps `"review_from"`, the snapshot its fix diff starts from (`references/gates.md`); a passed `M<n>/red` also keeps the failing test lines in `"output"` and, for a milestone with a `(zachowanie)` criterion, `"test_author": true` when `test-author` wrote those tests (`false` only with a deviation saying why). Increase `rounds` **before** running the check of that round, so an interrupted round still counts. After a third failed round `stuck` holds the `utknelo` file path. The script rejects a fourth round, and for a plan with `**Kryteria:**` a `journal` or `done` phase without a `qa` gate that passed or went stuck.
- `deferred` (optional, runs started before 1.6): `null`, or the path of the plan's `odlozone` file with milestone Suggestions. New runs do not create it: review notes go into the plan (`references/gates.md`).
- `deviations`: `{"milestone": "M2", "rule": 1-4, "note": "<what and why>"}`; rule 4 also has `"question": "loc/inbox/NNN-pytanie-….md"`.
- `next_action`: one concrete step, precise enough for someone who has read nothing else, e.g. `"Run the M2 proof: python -m pytest tests/test_export.py; expected 3 passed"`.

## Resuming

The file exists when the skill starts: validate it, read `next_action`, and continue from there. Say in one line where you resume. Do not repeat a step whose result is already recorded, and do not reset round counters.

## At the end

`plan` points to the plan's new place in `loc/inbox/done/`, `phase` goes `journal` while the diary entry is written and the commit made, then `done`. `commit` holds what `commit_plan.py` recorded: the hash, `none` (no file outside `loc/` changed) or `skipped: <reason>`; `done` needs it. The file stays: it is the record of the run. `loc/` is ignored by git.
