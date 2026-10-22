# {NNN} — {TITLE}

**Type:** stuck
**Category:** <blocking | non-blocking: the most serious finding left in the whole file>
**Status:** open
**Created:** {DATE}
**Source:** {SOURCE}
**Created by:** {BY}
**Stuck gates:** <every gate with a section below, e.g. `final-review`, `plan gate`>

<!-- One file per plan run, only for the final review and the plan gate:
a stuck milestone or QA gate is recorded in the plan's `## Stuck gates`.
Every stuck gate adds its own section (`## final-review`, `## plan gate`)
and adds itself to **Stuck gates:**. -->

## <gate, e.g. final-review>

**Gate:** <final review | plan gate> of <plan path>
**Architect (Triage):** <its verdict and reason in one or two sentences>
**Next:** <the new `deferred`, `question` or plan file, or "rounds 4–6">

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
<what closed it: the plan that fixed it, or the file it became>
