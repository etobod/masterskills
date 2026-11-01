# Review gates, the judge and review notes

## Categories

Every finding of a milestone's code-review and of the final review gets one category:

- **Blocking** (`blocking`): wrong behaviour, a broken `Invariants` entry, a criterion not met. code-review `high`.
- **Non-blocking** (`non-blocking`): a real defect in a rarer case that does happen. code-review `medium`.
- **Suggestion** (`suggestion`): real but minor: style, wording, a comment in the wrong place. code-review `low`.
- **Unrealistic** (`unrealistic`): the finding needs an input or a state that **nothing in this project produces**: not its code, not its real data, not a user mistake you can foresee. Ask "who or what here would produce this?" and name the answer: the code that writes that input and why it never writes this form (e.g. "the report is written by the model following `report-format.md`, which uses no numeric entities"). If you cannot name it, the finding is not unrealistic. An input produced only by someone listed in the plan's `## Not defended against` is Unrealistic: quote that line as the answer.

When code-review gives no severity, judge it by these definitions; never lower one to pass the gate. A finding keeps its category from the milestone to the final review unless there is a new argument, such as naming who produces the input; one settled by `Not defended against` is never raised again. Suggestions and Unrealistic findings are **never fixed in the gate**.

## Verdicts

Before the judge, give every finding a verdict from the code: `confirmed` (the code shows it); `needs_validation` (plausible, but the code alone cannot settle it, e.g. a race between two writes), which goes to the judge marked unconfirmed, never dropped; `rejected` (the code contradicts it), dropped with one line why. The gate keeps the last round's counts in `verdicts`.

## The judge

Every round, after categories and verdicts, the `judge` gets the Blocking and Non-blocking findings not `rejected` (each with `file:line` and category), the plan path, `loc/PRD.md` and `CLAUDE.md`. For each it answers `fix` or `enough` with a reason. Fix the `fix` ones. Each `enough` becomes an `enough` line in the plan (below) and is not fixed. The gate **passes when a round leaves nothing to fix**. Never overrule an `enough` to fix it anyway, and never fix a finding the judge was not shown. Telling the user about a round, list every finding the judge saw: the `fix` ones, then each `enough` with the judge's reason in one sentence.

**A challenged decision.** A `challenges D-NN` verdict is not fixed: the decision holds until the user changes it. Record it as `- enough (<gate>): <finding> Reason: challenges D-NN: <the argument>`. Then call the `architect` agent in Challenge mode with the finding, its argument, the plan path, `loc/PRD.md` and `CLAUDE.md`, and turn its report into a `question` file (`next_number.py --type question --by "architect (Challenge)"`, title `Decision D-NN: <topic>`) with its options, the recommended one first. Work goes on under the decision as it stands.

## Rounds 2 and 3 of a code-review

Review only the fixes. Before fixing, store the milestone's `end` snapshot in the gate as `"review_from"`, so a resumed run still has it. After fixing, `review_diff.py --from <review_from> --out loc/review/<NNN>-M<n>-r<round>.diff`, then:

```
Skill(skill: "code-review", args: "<files review_diff listed> medium — Review only the changes in <diff file>; check that these findings are fixed: <the ones the judge marked fix>. Do not review code outside the diff.")
```

Drop any finding whose `file:line` lies outside that diff's hunks. The final review still covers the whole plan.

## Review notes in the plan

Suggestions, Unrealistic findings and the judge's `enough` create **no inbox file**. Each becomes one line in the plan file, in a section `## Review notes` placed right before `## Resolution` (create it at the first note):

```
- suggestion (M2 code-review): `app.py:14` — the LINE_PREFIX comment sits above RAW_HTML
- unrealistic (final-review): `check.py:88` — the entity `&#51;` in a report shows 3 but counts 51. Who produces it: the model writes the report from report-format.md, which uses no entities
- enough (M8 code-review): `time.py:88` — "In the morning, around seven" gives 08:00. Reason: same part of day, the goal is patterns [Goal 2]
```

The gate is `M<n> code-review`, `final-review` or `planning` (judged by `loc-planning`). Only the finding, no proposed fix. An Unrealistic line ends with `Who produces it:` and the answer, an `enough` line with `Reason:`, the judge's reason and its PRD point; `check_state.py` rejects the section otherwise. A finding already listed as `enough` goes to the judge marked as already judged; without a new argument it stays `enough`, with no second line.

An older run's `deferred` file (in the state file) keeps getting its milestone Suggestions; close it as below.

A gate that fails its third round, and closing its file at the end of the plan: `references/stuck.md`.
