# Search milestones

A **search milestone** (`**Kind:** search`) improves a measured result toward a target within a budget of iterations. Missing the target is an accepted outcome, decided when the plan was written: it is never stuck. Every other milestone is a **proof milestone** (`**Kind:** proof`, the default, no line needed).

## Planning: which kind, and its fields

One test: can the result be stated as a proof that must pass? Then it is a proof milestone. Only a number to improve with an unknown ceiling ("raise the pass rate of the prompt", "find the fastest settings") is a search, and only when the requirement itself is such a number or the user or brainstorm asked for one. A search is never a way out of a hard proof. When unsure, the `architect` (Decide).

```
### M2 — best prompt for the classifier
**Kind:** search
**Metric:** `python -B eval/score.py` prints the pass rate of `eval/cases/`
**Target:** >= 80
**Budget:** 50
**Give up:** no gain in 8 tries in a row
**May change:** `prompts/classify.txt`
**Measure:** one run; the cases are deterministic
**Hold-out:** `eval/holdout/`, scored at the start and the end only
**Guard:** `python -m unittest` → `OK`
**Leads:** few-shot examples of the two confused classes; a fixed output format
**Proof:** `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/search_log.py --check --log loc/state/<NNN>/search-M2.md` → `ok`
```

- **Metric**: a command that prints one number. `Target`: `>= <n>` or `<= <n>`.
- **Budget**: 50 by default; set less when 50 is clearly too many. Over 50 needs the user's consent (`**Budget:** 80 — user approved <date>`).
- **Measure**: one run, or several and their median, when the result varies between runs. **Hold-out**: cases the search never sees, or `none` with the reason.
- **Guard** (optional): a command that must keep passing, usually the project's tests.
- **Leads**: where to look, gathered by the `researcher` agent (known techniques, what worked before in `loc/MEMORY.md`).
- No `**Criteria:**`: the metric is the test.

The plan's rubber-duck judges only the preparation (can the metric fail, are cases, budget, stop rule and leads set), never whether the target will be reached.

## Running it

Phase `search`, gate `M<n>/search` with `"log": "loc/state/<NNN>/search-M<n>.md"` (`rounds: 1`). The log script decides keep, revert and stop; never decide them yourself.

1. **Baseline.** Run the `Metric` (and the hold-out) as `Measure` says, on the untouched code. Then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/search_log.py --start --log <log> --metric "<command>" --baseline <score> --target "<target>" --budget <n> --give-up <n>`. A `stop` already set: the target is met; go to step 4.
2. **One iteration.** A fresh `searcher` agent, each time a new one: give it the milestone's text, the `Leads`, the `May change` files and the log. It returns one change with its hypothesis, a metric change proposal, or "give up" with a reason. Then you:
   - check that it changed only `May change` files (else revert, count the try as reverted);
   - run the `Metric` as `Measure` says, and the `Guard` if any; a failing guard counts as no gain;
   - `search_log.py --add --log <log> --score <score> --hypothesis "<...>" --change "<...>"`;
   - `keep: true`: commit the change (`search M<n>: <hypothesis>`); `false`: restore the `May change` files from the last commit.
3. **Until `stop` is set.** A `stop` of `target` ends the search even when the agent knows how to go further. "Give up" from the agent: `search_log.py --stop --reason "<reason>"`.
   - **Metric change**: the agent never edits the metric, cases, hold-out or guard; it proposes. Give the proposal to the `judge` agent ("does this fix a wrong case or scorer, or make the task easier?"). `fix`: make the change in its own commit, measure the baseline and the best again, `search_log.py --metric-change --log <log> --reason "<...>" --baseline <x> --best <x>`. At most 2; a third is refused and becomes a `question` file while the search goes on with the current metric.
4. **Close.** Measure the hold-out again. Run the `Proof`; the gate passes whatever score was reached. Then the code-review gate on the kept change, once, as step 5 of `SKILL.md`; with only text in `May change` (a prompt, a config value) record `M<n>/code-review` with `rounds: 0, passed: true`. No fix of a later gate changes the metric, cases, hold-out or guard.

## Summary

Under the milestone in the plan, and in the report:

```
**Search:** 20 → 64 (target >= 80), 50 of 50 iterations, stopped: budget; hold-out 18 → 55
**Could go further:** per-class examples for B and C; a shorter system part
```

A search that stopped below the target also creates a `deferred` file with the `Could go further` ideas, marked optional (`next_number.py --type deferred … --why "search stopped below the target" --by loc-orchestrate`), so they are not lost. After `/clear`, the log is where the search resumes: never restart it.
