# {NNN} — {TITLE}

**Type:** plan
**Status:** open
**Created:** {DATE}
**Source:** {SOURCE}
**Created by:** {BY}

## Goal
<what works after the plan is executed, in one paragraph>

## Out of scope
- <deliberately outside the scope>

## Not defended against
- <who or what produces input the code deliberately does not defend against, and why; `- none` when nothing>

## Code context
- `<file:line>` — <what is there and why it matters>

## Milestones

### M1 — <name>
<what is built>
**Criteria:**
- K1: <what the code must do> → `<test file::test name>`
<!-- A milestone that changes no code: instead of Criteria, `**No tests:** <reason>`. -->
**Performer:** auto
**Proof:** `<command>` → `<expected output>`
<!-- A search milestone (a number to improve, missing the target accepted): `**Kind:** search` and its fields instead of Criteria, see skills/loc-orchestrate/references/search.md. -->
<!-- Optional, only for what no command can see (look, feel, a real device), checked after the proof: `**Performer:** user (blocking)` or `user (deferrable)` and `**Manual check:** <what the user looks at>`. -->

## Risks and decisions
- <a risk or a decision, referring to B-xx or a `question` file>

## Plan gate
<record of the gate rounds: round, `check_plan.py` result, rubber-duck notes and what was fixed; at most 3 rounds>

## Resolution
<empty until handled: result of execution, date, commit>
