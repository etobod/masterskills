# Review gates, the judge and review notes

## Categories

Every finding of a milestone's quick code-review and of the final review gets one category:

- **Blocking** (`blocking`), checkable: a wrong result (a criterion not met is one), data lost or distorted, a crash or a hang, a failing proof or test, a test that cannot fail on the wrong result it guards (a criterion without a real test), a broken `## Invariants` entry of `CLAUDE.md`. Nothing else is blocking. code-review `high`.
- **Non-blocking** (`non-blocking`): any other real defect, in a case that does happen. code-review `medium`.
- **Suggestion** (`suggestion`): real but minor: style, wording, a comment in the wrong place. code-review `low`.
- **Unrealistic** (`unrealistic`): the finding needs an input or a state that **nothing in this project produces**: not its code, not its real data, not a user mistake you can foresee. Ask "who or what here would produce this?" and name the answer: the code that writes that input and why it never writes this form (e.g. "the report is written by the model following `report-format.md`, which uses no numeric entities"). If you cannot name it, the finding is not unrealistic. An input produced only by someone listed in the plan's `## Not defended against` is Unrealistic: quote that line as the answer.

The code-review names are a finding's severity, not the level a review runs at. When code-review gives no severity, judge it by these definitions; never lower one to pass the gate. A finding keeps its category from round to round unless there is a new argument, such as naming who produces the input; one settled by `Not defended against` is never raised again. A milestone gate fixes only Blocking findings; the final review fixes what the judge marks `fix`.

## Verdicts

Before the judge, give every finding a verdict from the code: `confirmed` (the code shows it); `needs_validation` (plausible, but the code alone cannot settle it, e.g. a race between two writes), which goes to the judge marked unconfirmed, never dropped; `rejected` (the code contradicts it), dropped with one line why. The gate keeps the last round's counts in `verdicts`.

## The milestone gate

After each milestone's `end` snapshot. No changed files: record `{"rounds": 0, "passed": true, "stuck": null}` and skip it. Otherwise increase `rounds`, then `Skill(skill: "code-review", args: "<changed files> low — also flag new code the project, its standard library, platform or dependencies already provide; in a test file, at any level, a test that cannot fail on wrong code: it compares with values copied from the source instead of taken from it, matches part of a value where the whole is meant, compares numbers as text, or re-implements a helper the code exports")`: always explicit files and level, **never `ultra`** (it leaves the machine). A lost report is asked for again (core rule 6a), never a relaunch. Give each finding a category and a verdict; no rubber-duck. Only a round with Blocking findings not `rejected` calls the `judge`, with those findings, the plan path, `loc/PRD.md` and `CLAUDE.md`, and one question per finding: "is it really blocking?" Fix the `fix` ones, rerun the milestone's proof and take a new `end` snapshot. A Non-blocking finding, and a Blocking one the judge called `enough`, is not fixed: append it to the gate's `"pending"` list as `"<file:line> — <category>: <finding>"`; the final review's judge gets it. A `challenges D-NN` follows "A challenged decision" below. Suggestions and Unrealistic findings become review notes at once, gate `M<n> code-review`. Rounds 2 and 3 review only the fixes (below). The gate passes when a round leaves nothing the judge marked `fix`; after a third failed round it is **stuck** (`references/stuck.md`).

## The judge

Every round of the final review (a milestone gate: above), after categories and verdicts, the `judge` gets the Blocking and Non-blocking findings not `rejected` (each with `file:line` and category), in round 1 also every milestone gate's `pending` finding the code still shows, the plan path, `loc/PRD.md` and `CLAUDE.md`. For each it answers `fix` or `enough` with a reason. Fix the `fix` ones. Each `enough` becomes an `enough` line in the plan (below) and is not fixed. The gate **passes when a round leaves nothing to fix**. Never overrule an `enough` to fix it anyway, and never fix a finding the judge was not shown. Telling the user about a round, list every finding the judge saw: the `fix` ones, then each `enough` with the judge's reason in one sentence.

**A challenged decision.** A `challenges D-NN` verdict is not fixed: the decision holds until the user changes it. Record it as `- enough (<gate>): <finding> Reason: challenges D-NN: <the argument>`. Then call the `architect` agent in Challenge mode with the finding, its argument, the plan path, `loc/PRD.md` and `CLAUDE.md`, and turn its report into a `question` file (`next_number.py --type question --by "architect (Challenge)"`, title `Decision D-NN: <topic>`) with its options, the recommended one first. Work goes on under the decision as it stands.

## Rounds 2 and 3

Review only the fixes. Before fixing, take a snapshot and store it in the gate as `"review_from"`, so a resumed run still has it. After fixing, `review_diff.py --from <review_from> --out loc/review/<NNN>-r<round>.diff` (a milestone gate: `<NNN>-M<n>-r<round>.diff`), then:

```
Skill(skill: "code-review", args: "<files review_diff listed> <level> — Review only the changes in <diff file>; check that these findings are fixed: <the ones being fixed>. Do not review code outside the diff.")
```

The level is `low` in a milestone gate, `medium` in the final review, where the `rubber-duck` gets the same diff file. Drop any finding whose `file:line` lies outside that diff's hunks.

## Review notes in the plan

Suggestions, Unrealistic findings and the judge's `enough` create **no inbox file**. Each becomes one line in the plan file, in a section `## Review notes` placed right before `## Resolution` (create it at the first note):

```
- suggestion (M2 code-review): `app.py:14` — the LINE_PREFIX comment sits above RAW_HTML
- unrealistic (final-review): `check.py:88` — the entity `&#51;` in a report shows 3 but counts 51. Who produces it: the model writes the report from report-format.md, which uses no entities
- enough (final-review): `time.py:88` — "In the morning, around seven" gives 08:00. Reason: same part of day, the goal is patterns [Goal 2]
```

The gate is `M<n> code-review`, `final-review`, `M<n> design` or `planning` (judged by `loc-planning`); plans of 2.30-2.31 also have `non-blocking` lines. Only the finding, no proposed fix. An Unrealistic line ends with `Who produces it:` and the answer, an `enough` line with `Reason:`, the judge's reason and its PRD point; `check_state.py` rejects the section otherwise. A finding already listed as `enough` goes to the judge marked as already judged; without a new argument it stays `enough`, with no second line.

An older run's `deferred` file (in the state file) keeps getting its milestone Suggestions; close it as below.

A gate that fails its third round, and closing its file at the end of the plan: `references/stuck.md`.
