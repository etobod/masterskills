# Search milestones

A **search milestone** (`**Kind:** search`) improves a measured result toward a target within a budget of tries; missing the target is accepted, never stuck. Every other milestone is a **proof milestone** (the default).

## Planning: which kind, and its fields

A search only for a number to improve with an unknown ceiling (a pass rate, a run time) that the requirement or the user asks for; never a way out of a hard proof. Unsure: the `architect` (Decide).

```
### M2 — best prompt for the classifier
**Kind:** search
**Metric:** `python -B eval/score.py` prints the pass rate of `eval/cases/`
**Quick metric:** `python -B eval/score.py --failed` (the 30 cases plan 041 failed, 2 min)
**Baseline:** 64, plan 041's run of the same metric on the same code
**Target:** >= 80
**Budget:** 50
**Give up:** no gain in 8 tries in a row
**May change:** `prompts/classify.txt`
**Measure:** one run; deterministic cases
**Hold-out:** `eval/holdout/`, scored at the end only
**Leads:** few-shot examples of the two confused classes; a fixed output format
**Proof:** `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/search_log.py --check --log loc/state/<NNN>/search-M2.md` → `ok`
```

- **Metric**: a command that prints one number. `Target`: `>= <n>` or `<= <n>`.
- **Budget**: 50 by default (20 from a Triage `search`), less when 50 is clearly too many; over 50 only with the user's consent (`**Budget:** 80 — user approved <date>`).
- **Hold-out**: cases the search never sees, or `none` with the reason. Optional **Guard**: a command that must keep passing. **Leads**: from the `researcher` agent. No `**Criteria:**`.

### Measure in proportion to the work

Measuring serves the tries, never the other way round. Stop at the first rung that works:

1. **Is the number already known?** An earlier plan, a log, the user's results: `**Baseline:**` names it, and nothing is measured before the first try.
2. **Quick metric**: when the full metric takes longer than making a change, a smaller set that moves first: earlier failures plus a few passing cases. Otherwise `same as Metric` with the reason. Measuring grows with progress: minutes first; a wider set only once gains show (a metric change).
3. **Full metric** only to confirm a quick gain that meets the target, and once at the end. Repeated runs (`Measure`) and the hold-out only at the end, never per try, never a grid of settings up front.

The plan's rubber-duck judges only this preparation, never whether the target will be reached.

## Running it

Phase `search`, gate `M<n>/search` with `"log": "loc/state/<NNN>/search-M<n>.md"` (`rounds: 1`). `search_log.py` decides keep, revert and stop, never you.

1. **Start.** Take the `Baseline` as written; measure only what it says is missing, with the quick metric. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/search_log.py --start --log <log> --metric "<command>" [--quick "<command>"] --baseline <score> --target "<target>" --budget <n> --give-up <n>`.
2. **One try.** A fresh `searcher` agent with the milestone, the `May change` files and the log returns one change and its hypothesis, a metric change proposal, or "give up". Then you:
   - check it changed only `May change` files (else revert; the try counts as reverted);
   - run the quick metric (or the metric), and the `Guard` if any; a failing guard is no gain;
   - `search_log.py --add --log <log> --score <score> --hypothesis "<...>" --change "<...>"`;
   - `keep: true`: commit (`search M<n>: <hypothesis>`); `false`: restore the `May change` files.
   - `confirm: true`: run the full metric, `search_log.py --confirm --log <log> --full <score>`.
3. **Until `stop` is set.** `target` ends it even when more is possible. "Give up": `search_log.py --stop --reason "<reason>"`; time spent measuring is never a reason.
   - **Metric change**: the agent never edits the metric, cases, hold-out or guard; it proposes. The `judge` decides ("does this fix a wrong case or scorer, or make the task easier?"). `fix`: change it in its own commit, re-measure baseline and best, `search_log.py --metric-change --log <log> --reason "<...>" --baseline <x> --best <x>`. A third change is refused and becomes a `question` file; the search goes on.
4. **Close.** The full metric on the best, if not confirmed yet, and the hold-out. Run the `Proof`; the gate passes whatever score was reached. Then the code-review gate on the kept change, once (step 5 of `SKILL.md`); with only text in `May change` (a prompt, a config value) record `M<n>/code-review` as `rounds: 0, passed: true`. No later fix changes the metric, cases, hold-out or guard.

## Summary

Under the milestone and in the report:

```
**Search:** 64 → 78 (target >= 80), 50 of 50 tries, stopped: budget; hold-out 61
**Could go further:** per-class examples for B and C; a shorter system part
```

Below the target, the ideas also go into a `deferred` file, marked optional (`next_number.py --type deferred … --why "search stopped below the target" --by loc-orchestrate`). After `/clear`, the search resumes from the log: never restart it.
