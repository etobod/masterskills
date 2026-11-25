# Review gates, the judge and review notes

## Categories

Every finding of the final review gets one category:

- **Blocking** (`blocking`), checkable: a wrong result (a criterion not met is one), data lost or distorted, a crash or a hang, a failing proof or test, a broken `## Invariants` entry of `CLAUDE.md`. Nothing else is blocking. code-review `high`.
- **Non-blocking** (`non-blocking`): any other real defect, in a case that does happen. code-review `medium`.
- **Suggestion** (`suggestion`): real but minor: style, wording, a comment in the wrong place. code-review `low`.
- **Unrealistic** (`unrealistic`): the finding needs an input or a state that **nothing in this project produces**: not its code, not its real data, not a user mistake you can foresee. Ask "who or what here would produce this?" and name the answer: the code that writes that input and why it never writes this form (e.g. "the report is written by the model following `report-format.md`, which uses no numeric entities"). If you cannot name it, the finding is not unrealistic. An input produced only by someone listed in the plan's `## Not defended against` is Unrealistic: quote that line as the answer.

When code-review gives no severity, judge it by these definitions; never lower one to pass the gate. A finding keeps its category from round to round unless there is a new argument, such as naming who produces the input; one settled by `Not defended against` is never raised again. Only Blocking findings are fixed in the gate.

## Verdicts

Before the judge, give every finding a verdict from the code: `confirmed` (the code shows it); `needs_validation` (plausible, but the code alone cannot settle it, e.g. a race between two writes), which goes to the judge marked unconfirmed, never dropped; `rejected` (the code contradicts it), dropped with one line why. The gate keeps the last round's counts in `verdicts`.

## The judge

Only a round with Blocking findings calls the `judge`: it gets those not `rejected` (each with `file:line` and category), the plan path, `loc/PRD.md` and `CLAUDE.md`, and answers one question per finding, "is it really blocking?": `fix`, or `enough` (not blocking) with a reason. Fix the `fix` ones. Each `enough` becomes an `enough` line in the plan (below) and is not fixed. Non-blocking findings never go to the judge and are never fixed in the gate. The gate **passes when a round leaves nothing to fix**. Never overrule an `enough` to fix it anyway, and never fix a finding the judge was not shown. Telling the user about a round, list every finding the judge saw: the `fix` ones, then each `enough` with the judge's reason in one sentence.

**A challenged decision.** A `challenges D-NN` verdict is not fixed: the decision holds until the user changes it. Record it as `- enough (<gate>): <finding> Reason: challenges D-NN: <the argument>`. Then call the `architect` agent in Challenge mode with the finding, its argument, the plan path, `loc/PRD.md` and `CLAUDE.md`, and turn its report into a `question` file (`next_number.py --type question --by "architect (Challenge)"`, title `Decision D-NN: <topic>`) with its options, the recommended one first. Work goes on under the decision as it stands.

## Rounds 2 and 3

Review only the fixes. Before fixing, take a snapshot and store it in the gate as `"review_from"`, so a resumed run still has it. After fixing, `review_diff.py --from <review_from> --out loc/review/<NNN>-r<round>.diff`, then:

```
Skill(skill: "code-review", args: "<files review_diff listed> medium — Review only the changes in <diff file>; check that these findings are fixed: <the ones the judge marked fix>. Do not review code outside the diff.")
```

The `rubber-duck` gets the same diff file. Drop any finding whose `file:line` lies outside that diff's hunks.

## Review notes in the plan

Non-blocking findings, Suggestions, Unrealistic findings and the judge's `enough` create **no inbox file**. Each becomes one line in the plan file, in a section `## Review notes` placed right before `## Resolution` (create it at the first note):

```
- non-blocking (final-review): `sync.py:52` — a retry after a timeout logs the error twice
- suggestion (final-review): `app.py:14` — the LINE_PREFIX comment sits above RAW_HTML
- unrealistic (final-review): `check.py:88` — the entity `&#51;` in a report shows 3 but counts 51. Who produces it: the model writes the report from report-format.md, which uses no entities
- enough (final-review): `time.py:88` — "In the morning, around seven" gives 08:00. Reason: same part of day, the goal is patterns [Goal 2]
```

The gate is `final-review`, `M<n> design` or `planning` (judged by `loc-planning`); older plans also have `M<n> code-review`. Only the finding, no proposed fix. An Unrealistic line ends with `Who produces it:` and the answer, an `enough` line with `Reason:`, the judge's reason and its PRD point; `check_state.py` rejects the section otherwise. A finding already listed as `enough` goes to the judge marked as already judged; without a new argument it stays `enough`, with no second line.

**A repeated non-blocking finding.** When the same file and the same rule already have a `non-blocking` line in an earlier plan's `## Review notes`, write no second line: add a `### Repeated non-blocking findings` matter to the plan's one `question` file, each repeat with both plans, the options `fix it in a plan` and `accept it`.

An older run's `deferred` file (in the state file) keeps getting its milestone Suggestions; close it as below.

A gate that fails its third round, and closing its file at the end of the plan: `references/stuck.md`.
