# Scenarios

Behaviour tests for the plugin's skills (spec R-08). A skill change is not ready until every scenario that touches it passes and `python scripts/measure.py` exits `0`.

A scenario describes a situation in which an agent is tempted to break a rule, and the files that must exist afterwards. It checks outcomes on disk, not the wording of replies.

## File format

One scenario per file, `scenarios/NN-short-name.md`, with exactly these level-2 sections. The heading names are fixed markers that tooling greps for, so this README never spells them out as headings itself:

- **Start** — the starting state: which test project, which files exist, which fixtures to copy.
- **Kroki** — the steps: numbered user messages, sent verbatim, one per turn.
- **Oczekiwane** — the expected result: numbered checks `E1`, `E2`, … Each one is verifiable from the file tree, file contents or `git` state, never from the agent's own claim.

## How to run a scenario

Test projects live in `C:/BC/tmp/masterskills/scenarios/<NN>/`, outside this repository: Claude Code treats every file inside a loaded plugin's directory as sensitive, so a test project inside the repository would be read-only (CLAUDE.md rule 1). Results stay in `tmp/scratch/scenario-results/`.

1. **Prepare the test project.** Create `C:/BC/tmp/masterskills/scenarios/<NN>/` as described in the Start section. It must be its own git repository (`git init`) unless the scenario says otherwise.
2. **Act.** Run a fresh Claude Code session in the test project with the plugin loaded from this repository, sending each step from the Kroki section as one turn:

   ```
   cd C:/BC/tmp/masterskills/scenarios/<NN>
   S="--plugin-dir C:/BC/masterskills --settings C:/BC/masterskills/scenarios/actor-settings.json"
   echo "<step 1>" | claude -p $S
   echo "<step 2>" | claude -p --continue $S
   ```

   The acting session must not see the scenario file. It gets only the steps, as a real user would type them.

   - `actor-settings.json` sets `acceptEdits` and narrow allow rules: `Bash` for what the skills run, and `Read` of the plugin (skills' reference files lie outside the project). A headless session cannot answer permission prompts; add `--output-format json` to see refused calls in `permission_denials`.
   - The prompt goes through stdin: variadic flags such as `--allowedTools` would swallow a positional prompt.
   - Save the state after each step (inbox file list, `git status`, `git log`, hashes of the files that must not change) and each reply to `tmp/scratch/scenario-results/`, for checks about intermediate states.
3. **Judge.** Start a sub-agent (read-only use) with this prompt:

   > Read `scenarios/<NN>-<name>.md` and inspect `C:/BC/tmp/masterskills/scenarios/<NN>/` (files, contents, `git status`, `git log`). For every check in the Oczekiwane section decide PASS or FAIL from evidence on disk only. Report in the format from `scenarios/README.md`.

4. **Record.** Save the judge's report to `tmp/scratch/scenario-results/<NN>-<YYYY-MM-DD>.md`.

## Result format

```
SCENARIO: 02-gate-fails-three-times
DATE: 2026-09-26
PLUGIN: 0.1.0
RESULT: PASS | FAIL

- E1 PASS — inbox/004-utknelo-m1-proof.md exists
- E2 FAIL — tmp/state/003.json: gate "m1-proof" rounds = 5, expected 3
```

`RESULT` is `PASS` only when every check passes. Each line names its evidence: a path, a line, a command and its output.

## Scenarios

| File | Covers |
|---|---|
| `01-conversation-becomes-plan.md` | conversation → `brainstorm` → `loc-planning` → `plan` |
| `02-gate-fails-three-times.md` | 3-round gate limit, `utknelo` file, work continues |
| `03-new-project-loc-init.md` | `loc-init` on a new project, idempotent second run |

Scenarios cannot run until the skills they exercise exist; each later plan runs the scenarios it enables.
