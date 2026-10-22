# PRD — {PROJECT}

What the project is for and where it is heading. Only what is current.

- `## Goal`, `## Core idea` and `## Scenarios` are fixed: they never move into a plan. The
  review judge weighs by them what a fix really gives the project. `loc-planning`
  proposes every change to them in conversation and writes it only after the
  user agrees.
- `## Directions` are ideas waiting for a plan. The fragment a plan is made from
  moves in full into that plan's `## PRD fragment` section and disappears from here.
  What was done is told by `loc/MEMORY.md`.
- `## Decisions` are lasting choices later plans follow and cite (`D-01`)
  instead of restating them. `loc-planning` adds one after the user agrees.
- `## Priorities` is written only by the user. The `pm` agent orders the
  queue of plans by it.
- `## Course` appears at the end while `loc-director` works: the course the user
  agreed, its limit and next step. Only `scripts/course.py` and the Stop hook
  change it.

## Goal
<what this project is for and for whom; a few sentences or a short numbered list>

## Core idea
<!-- A few points the project stands on: a goal or a priority with its reason, not
a description of the code and not a repeat of `Invariants` in `CLAUDE.md`. Example:
- **Data is the foundation.** Every word of the user is kept in the original
  and can be processed again after changes, without typing it again.
-->

## Scenarios
<!-- 3–7 ways of use the project must support: who, what they do, what they
expect. The judge checks whether a finding breaks one of them. Not a list of
features: new features are `## Directions` and plan criteria. Example:
1. The user dictates a note on the run and in the evening sees it in the journal
   with the right time of day.
-->

## Decisions
<!-- Lasting decisions plans follow instead of restating them, one line each:
- D-01: <decision>. Reason: <why>. (<date>)
A replaced decision is removed; the one that replaces it says `replaces D-01: <why>`.
Example:
- D-01: Notes are stored as NDJSON, one note per line. Reason: an append never
  rewrites the file. (2026-10-18)
-->

## Priorities
<!-- Written only by the user: what matters most now. The `pm` agent orders the plans by it. Example:
- Reliable import first, new reports later.
-->

## Directions
### <fragment name>
<what should be built and why>
