# {NNN} — {TITLE}

**Type:** stuck
**Category:** <blocking | non-blocking: the most serious finding left in the whole file>
**Status:** open
**Created:** {DATE}
**Source:** {SOURCE}
**Created by:** {BY}
**Stuck gates:** <every gate with a section below, e.g. `M1 code-review` (milestone), `final-review`>

<!-- One file per plan execution: every stuck gate adds its own section
`## M<n> <gate>` (or `## qa`, `## final-review`) with the same subsections,
and adds itself to **Stuck gates:**. The plan gate in loc-planning has one
section `## plan gate`. -->

## <gate, e.g. M2 code-review>

**Gate:** <milestone M2 code-review | final review | QA | plan gate> of <plan path>
**Architect (<Challenge | Triage>):** <its verdict and recommendation in one or two sentences>
**Next:** <what happens to what remains, e.g. "a later milestone may fix it; checked against the code after the final review", or the new `deferred` / `question` file>

### What remains
<findings unresolved after 3 rounds, each with `file:line`>

### Rounds
#### Round 1
<the error output word for word, also when it repeats the previous round; what was changed; result>
#### Round 2
<the error output word for word, also when it repeats the previous round; what was changed; result>
#### Round 3
<the error output word for word, also when it repeats the previous round; what was changed; result>

### What happened next
<whether the rounds went in circles; which version of the code the work continued with; the architect's full report>

## Resolution
<empty until the user reads it and decides>
