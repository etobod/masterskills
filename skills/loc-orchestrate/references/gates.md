# Review gates, the judge and review notes

## Categories

Every finding of a milestone's code-review and of the final review gets one category:

- **Blocking** (`blokująca`): wrong behaviour, a broken `Invariants` entry, a criterion not met. code-review `high`.
- **Non-blocking** (`nieblokująca`): a real defect in a rarer case that does happen. code-review `medium`.
- **Suggestion** (`sugestia`): real but minor: style, wording, a comment in the wrong place. code-review `low`.
- **Unrealistic** (`nierealna`): the finding needs an input or a state that **nothing in this project produces**: not its code, not its real data, not a user mistake you can foresee. Ask "who or what here would produce this?" and name the answer: the code that writes that input and why it never writes this form (e.g. "the report is written by the model following `report-format.md`, which uses no numeric entities"). If you cannot name it, the finding is not unrealistic. An input produced only by someone listed in the plan's `## Nie bronimy przed` is Unrealistic: quote that line as the answer.

When code-review gives no severity, judge it by these definitions; never lower one to pass the gate. A finding keeps its category from the milestone to the final review unless there is a new argument, such as naming who produces the input; one settled by `Nie bronimy przed` is never raised again. Suggestions and Unrealistic findings are **never fixed in the gate**: fixing them round after round widens the plan and never ends.

## The judge

Every round, after the findings are categorised, the `judge` agent gets the Blocking and Non-blocking ones (each with `file:line` and category), the plan path, `loc/PRD.md` and `CLAUDE.md`. For each it answers `fix` or `enough` with a reason. Fix the `fix` ones. Each `enough` becomes a `dość` line in the plan (below) and is not fixed. The gate **passes when a round leaves nothing to fix**. Never overrule an `enough` to fix it anyway, and never fix a finding the judge was not shown.

## Rounds 2 and 3 of a code-review

Review only the fixes. Before fixing, store the milestone's `end` snapshot in the gate as `"review_from"`, so a resumed run still has it. After fixing, `review_diff.py --from <review_from> --out loc/review/<NNN>-M<n>-r<round>.diff`, then:

```
Skill(skill: "code-review", args: "<files review_diff listed> medium — Review only the changes in <diff file>; check that these findings are fixed: <the ones the judge marked fix>. Do not review code outside the diff.")
```

Drop any finding whose `file:line` lies outside that diff's hunks. The final review still covers the whole plan.

## Review notes in the plan

Suggestions, Unrealistic findings and the judge's `enough` create **no inbox file**. Each becomes one line in the plan file, in a section `## Uwagi z przeglądów` placed right before `## Rozstrzygnięcie` (create it at the first note):

```
- sugestia (M2 code-review): `app.py:14` — komentarz LINE_PREFIX stoi nad RAW_HTML
- nierealna (final-review): `check.py:88` — encja `&#51;` w raporcie pokaże 3, a liczy 51. Kto to wytwarza: raport pisze model według report-format.md, który nie używa encji
- dość (M8 code-review): `time.py:88` — „Rano, około siódmej” daje 08:00. Powód: pora dnia ta sama, cel to schematy [Cel 2]
```

The gate is `M<n> code-review` or `final-review`. Only the finding: no proposed fix, no "when to come back". An Unrealistic line ends with `Kto to wytwarza:` and the answer, a `dość` line with `Powód:`, the judge's reason and its PRD point; `check_state.py` rejects the section otherwise. A finding already listed as `dość` goes to the judge marked as already judged; it stays `enough` without a new argument, and never gets a second line.

A run started on an older version may have a `deferred` `odlozone` file in the state file: keep appending its milestone Suggestions there, and close it as below.

A gate that fails its third round, and closing its file at the end of the plan: `references/stuck.md`.
