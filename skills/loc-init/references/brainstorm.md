# Filling the project from a brainstorm

The brainstorm describes the project and the work to do. `loc-init` takes only the **frame**: what the project is for, the points it stands on, how it is used, its commands and limits. Ideas and features are work: they stay in the brainstorm for `loc-planning`, which makes the plan from the same file.

## What you may write

Only the sections listed in the script's `empty` field:

- `loc/PRD.md`: `Goal`, `Core idea`, `Scenarios`. Never `Directions`. A section listed but without its heading (an older PRD): add the heading from `${CLAUDE_PLUGIN_ROOT}/templates/loc/PRD.md` before `## Directions`.
- `CLAUDE.md`: any listed section.

A section not in `empty` already has the user's content: never change it, even when the brainstorm says something else. List each such difference in the report instead.

Replace the section's template comment or placeholder with the content; keep the heading. Everything is written in English.

## Where the content comes from

- **Sources:** the decisions under `## Decisions` (`B-xx`) and the facts under `## Notes`. A struck-through decision does not count. When two decisions disagree, the higher number wins.
- **Not a source:** `## Otwarte`, your own ideas, other projects.
- **Every point** ends with its source, e.g. `(B-03)`, or `(Notes)`.
- **A section the brainstorm says nothing about** stays empty. Do not fill it with a guess.
- **`Commands`:** only commands written in the brainstorm, character for character. Skills run them and never guess, so a made-up command breaks every later plan.

Where things go:

| The brainstorm says | Section |
|---|---|
| what the project is for, for whom | PRD `Goal` |
| a priority or principle with its reason | PRD `Core idea` |
| who uses the project, what they do and expect to see | PRD `Scenarios`, 3–7 numbered |
| how to build, test, run | `Commands` |
| a rule every change must keep | `Invariants` |
| how a person checks the result | `Manual verification / UAT` |
| a convention the code does not show | `Developer notes` |
| what is not allowed (cloud, data, costs) | `Limits` |
| a feature, an idea, a task | nowhere: it is for `loc-planning` |

`Goal` is never left empty: the brainstorm's `## Topic` always says what the project is.

## Check

After filling, run once: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/init_project.py --project "<dir>" --check`. It writes nothing. Each section still in `empty` must be one the brainstorm has nothing for; fill the others. Each section in `not_english` holds Polish: translate it.

## The brainstorm itself

Read it only. Do not edit, move or close it: `loc-planning` closes it when it makes the plan. Create no plan and no inbox file.

## Report

After the usual report, add:

- each section you filled, with its source numbers;
- `Goal`, `Core idea` and `Scenarios` word for word: they guide every review, so the user checks them now;
- each difference between the brainstorm and a section that was already filled;
- each empty section the brainstorm had nothing for;
- the next step: `/masterskills:loc-planning <NNN>` turns the rest of the brainstorm into a plan.
