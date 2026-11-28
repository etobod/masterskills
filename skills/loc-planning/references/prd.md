# Keeping `loc/PRD.md` current

`loc/PRD.md` holds only what is current. `## Goal`, `## Core idea` and `## Scenarios` are the project's guidelines: they never move into a plan, and the `judge` agent weighs review findings against them. `## Directions` are ideas waiting for a plan. Whatever stops being current leaves the PRD and goes into the plan that made it stale, so its history sits next to the reason.

Take the date with `date "+%Y-%m-%d"`. `loc/` is not in git: nothing removed from the PRD may be lost, so copy it into the plan **before** removing it; before a plan exists, the `PRD:` question holds it.

## A `Directions` fragment becomes a plan

1. Copy the fragment, heading and text unchanged, into the plan under a `## PRD fragment` section placed before `## Resolution`, with a first line `Moved from loc/PRD.md <date>.`
2. Remove the fragment from the PRD.

**Old markers.** A PRD written before this rule may still hold fragments marked `→ moved to loc/inbox/NNN-plan-….md`. Whenever you plan, move each such fragment the same way into the plan the marker names (in `loc/inbox/` or `loc/inbox/done/`), and remove it from the PRD. If that plan no longer exists, move it into the plan you are writing.

**Old header.** A header (the text before the first `##`) that still explains `→ moved to` markers is replaced by the header of `${CLAUDE_PLUGIN_ROOT}/templates/loc/PRD.md`, keeping any line that points to the project's decisions.

**Other sections.** A section that is neither `Goal`, `Core idea`, `Scenarios` nor `Directions` (e.g. a list of features to cut): check each point against the code. A point already done moves, copied word for word, into the `## PRD fragment` of the plan that did it; when you cannot name that plan, it stays. A section left empty is removed.

## `Goal`, `Core idea` and `Scenarios`

**Before the plan** (SKILL.md §2 step 5), compare the input with these three sections, `## Decisions` and the `Invariants`, `Limits` and `## Frontend` of `CLAUDE.md`; after the gate, once more for what only the plan added:

- **The plan changes them**: it adds a goal, drops one, or makes a point untrue (e.g. a plan that sends data to a server, against "data never leave the machine").
- **They are thin**: a point the input or the plan shows to be missing, e.g. a goal the brainstorm decided that the judge would otherwise reject as out of scope. Empty sections were filled before planning (`${CLAUDE_PLUGIN_ROOT}/skills/loc-init/references/frame.md`).

First create a `question` file (`next_number.py --type question --source "<input file, or the plan after its gate>" --by loc-planning`, title starting `PRD:`) with the proposed points, the old wording of every point that changes or goes, proposed `D-NN` lines and `CLAUDE.md` changes, and the line `After the answer: write loc/PRD.md and CLAUDE.md (the old wording stays here), then /masterskills:loc-planning <input NNN>, whose plan copies the old wording into its ## PRD fragment` (after the gate: `copy the old wording into the ## PRD fragment of plan <NNN>`). `loc-orchestrate` does not start while it is open: the judge must not weigh findings against stale guidelines. Then **ask the user with `AskUserQuestion`**. Show the points as they would read after the change, and ask two things: do they say what you want from the project, and do the technical points still hold, so that a defect the judge waves through cannot bring something down. A point is a goal or a priority with its reason, never a description of the code, and never a repeat of `Invariants`, which the judge reads anyway. When there are more than about fifteen, propose merging some.

- **Yes**: write the PRD and `CLAUDE.md`, then close the `question` (rule 8) and plan; the plan's `## PRD fragment` gets the old wording of each removed or rewritten point.
- **Changes**: apply them to the `question` and ask again.
- **No**: leave the files as they are, close the `question` with that answer and plan against them, naming the refused point in `## Risks and decisions`. Do not propose the same again unless the user asks; the closed `PRD:` files in `loc/inbox/done/` record what was refused.
- **No answer in this session**: the `question` stays open and, before the plan, no plan is written; whoever handles the answer later follows its last line, then plans.

## `Decisions`

A lasting choice later plans must follow (a format, a threshold) is a line `- D-NN: <decision>. Reason: <why>. (<date>)`, numbered after the last `D-`. Plans cite it (`D-03`) instead of restating it. One the input settles is asked before the plan, with the points above. Any other proposed decision goes into one question file, never only into the report (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type question --slug "decisions" --title "Decision: <topic>" --source "<plan path>" --by loc-planning`): each ready `D-NN` line with its practical effect, ending with the line `After the answer: write the approved lines to loc/PRD.md ## Decisions.` A plan that changes a decision gives the new one the next number with `replaces D-03: <why>`, and moves the old line verbatim into its `## PRD fragment`.

Nothing else in the PRD changes: no status, no summary, no milestone list.
