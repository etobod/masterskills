# Test plan

The project's test contract, about one page. It changes only through a plan
milestone (`loc-planning`), never on the side. `loc-qa` reports gaps but does not
edit it. No history of rounds and no requirement coverage.

## (a) Layers and commands

<!-- One line per layer: name, command, gate or report, fast or full.
A "gate" layer must pass for the plan to be approved; a "report" only informs.
Mark layers that run only in CI as "CI only": they are not part of the verdict.
Example:
| Layer | Command | Kind | When |
|---|---|---|---|
| unit | `python -m pytest tests/unit -q` | gate | fast, after every milestone |
| integration | `python -m pytest tests/integration -q` | gate | full, in `loc-qa` |
| model behaviour | `python evals/run.py` | report | on demand |
| ui | `ui_check.py --url <page> --widths <widths> --check` and `--tokens <file> --files <changed>`, from `## Frontend` in `CLAUDE.md` | gate | fast, after every UI milestone |
| screenshots | `ui_check.py --url <page> --widths <widths> --out loc/tmp/design/shots`, from `## Frontend` | gate | full, in `loc-qa` |
-->

## (b) What changed → what to extend

<!-- Tests only. Documents belong in `## Project-specific workflow` in `CLAUDE.md`.
Example:
| Change in the product | What to extend |
|---|---|
| new API endpoint | contract test in `tests/api/` + an entry in `qa-api` |
| new configuration option | test of the default and of an invalid value |
-->

## (c) Fixed matrices

<!-- Combinations every change in an area must pass, e.g. systems × versions. -->

## (d) Limits

<!-- What we deliberately do not check automatically, and why. -->

## (e) What a test looks like here

<!-- 3–7 lines of conventions:
- framework and assertion style;
- where tests go (directory, file names);
- fixtures: only hand-written ones in git; recorded data only in an ignored directory;
- tests with random data (e.g. hypothesis): a fixed seed or a deterministic mode, so the gate does not fail at random;
- marker of a known defect (e.g. `@pytest.mark.xfail(strict=True, reason="loc/inbox/NNN-…")`);
- directory of recorded data.
-->
