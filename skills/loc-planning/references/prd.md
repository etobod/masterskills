# Keeping `loc/PRD.md` current

`loc/PRD.md` holds only what is current. `## Goal`, `## Core idea` and `## Scenarios` are the project's guidelines: they never move into a plan, and the `judge` agent weighs review findings against them. `## Directions` are ideas waiting for a plan. Whatever stops being current leaves the PRD and goes into the plan that made it stale, so its history sits next to the reason.

Take the date with `date "+%Y-%m-%d"`. `loc/` is not in git: nothing removed from the PRD may be lost, so copy it into the plan **before** removing it.

## A `Directions` fragment becomes a plan

1. Copy the fragment, heading and text unchanged, into the plan under a `## PRD fragment` section placed before `## Resolution`, with a first line `Moved from loc/PRD.md <date>.`
2. Remove the fragment from the PRD.

**Old markers.** A PRD written before this rule may still hold fragments marked `→ moved to loc/inbox/NNN-plan-….md`. Whenever you plan, move each such fragment the same way into the plan the marker names (in `loc/inbox/` or `loc/inbox/done/`), and remove it from the PRD. If that plan no longer exists, move it into the plan you are writing.

**Old header.** A header (the text before the first `##`) that still explains `→ moved to` markers is replaced by the header of `${CLAUDE_PLUGIN_ROOT}/templates/loc/PRD.md`, keeping any line that points to the project's decisions.

**Other sections.** A section that is neither `Goal`, `Core idea`, `Scenarios` nor `Directions` (e.g. a list of features to cut): check each point against the code. A point already done moves, copied word for word, into the `## PRD fragment` of the plan that did it; when you cannot name that plan, it stays. A section left empty is removed.

## `Goal`, `Core idea` and `Scenarios`

After the plan's gate, before the report, compare the plan with these three sections:

- **The plan changes them**: it adds a goal, drops one, or makes a point untrue (e.g. a plan that sends data to a server, against "data never leave the machine").
- **They are missing or empty**: propose them from the PRD, the project's `CLAUDE.md` and the plans in `loc/inbox/done/`. The question is what the user wants to get from the project, not what the code does. `Scenarios`: 3–7 numbered, each who uses the project, what they do and what they expect to see, taken from the brainstorm, the `(behaviour)` criteria of done plans and what the code lets a user do. A missing heading goes before `## Directions`.

First create a `question` file (`next_number.py --type question`, title starting `PRD:`) with the proposed points, the old wording of every point that changes or goes, the plan's path, and the line `Po zgodzie: stare brzmienie do ## PRD fragment planu <NNN>, potem zapis loc/PRD.md.` `loc-orchestrate` does not start while it is open: the judge must not weigh findings against stale guidelines. Then **ask the user in the conversation**. Show the points as they would read after the change, and ask two things: do they say what you want from the project, and do the technical points still hold, so that a defect the judge waves through cannot bring something down. A point is a goal or a priority with its reason, never a description of the code, and never a repeat of `Invariants`, which the judge reads anyway. When there are more than about fifteen, propose merging some.

- **Yes**: copy the old wording of each removed or rewritten point into the plan's `## PRD fragment`, write the PRD, then close the `question` (rule 8).
- **Changes**: apply them to the `question` and ask again.
- **No**: leave the PRD as it is and close the `question` with that answer. Do not propose the same again unless the user asks; the closed `PRD:` files in `loc/inbox/done/` record what was refused.
- **No answer in this session**: the `question` stays open; whoever handles the answer later follows its last line.

Nothing else in the PRD changes: no status, no summary, no milestone list.
