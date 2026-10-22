# Harvest — the architect's steps

The `architect` agent reads this file in Harvest mode. `## Decisions` in `loc/PRD.md` is still empty and `loc/inbox/done/` holds finished plans.

Read each plan's `## Risks and decisions`, `## Review notes` and `## Resolution`, oldest first.

A decision is a lasting choice later plans must follow: a format, a threshold, a rule for reading data, a boundary of what the code handles. Not one: a detail of one plan, or an entry in `Invariants`.

1. **Candidates.** Each a ready `D-NN` line, numbered, with the plans that state or rely on it (`plan 044, 066`).
2. **Reversed.** A choice the plans changed back and forth: the plans in order with what each said, the code now (`file:line`), and the version you recommend.
3. **Contradictions** with `Goal`, `Core idea` or `Invariants`.
