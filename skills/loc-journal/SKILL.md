---
name: loc-journal
description: Use after work that changed something, to record it in loc/MEMORY.md — after a review, a plan finished by hand, a fix outside any plan or an important decision (e.g. "loc-journal", "zapisz w dzienniku"). Also tidies contradicting entries in loc/PATTERNS.md.
argument-hint: "[loc/inbox/done file | what was done]"
---

# loc-journal

Keeps the project's diary, `loc/MEMORY.md`: what was done, newest first, one short entry per piece of work, so anyone can find it again by topic and date. The diary records history; the code stays the truth about the present.

**Do not touch `loc/PRD.md`.**

## 1. What to record

`$ARGUMENTS` is a `loc/inbox/done/` file (a plan, a review, a question) or a description of the work. No argument: take the work just finished in this session. One entry per piece of work, of one type:

| Type | When |
|---|---|
| `Plan` | a plan was executed by hand (a plan run through orchestration writes its own entry) |
| `Planning` | a plan was made by hand (`loc-planning` writes its own entry) |
| `Review` | a review was done (`loc-review` on its own) |
| `Fix` | a change outside any plan that actually changed something |
| `Decision` | an important decision, e.g. an answered `question` that changes direction |

Nothing changed (a conversation, a question, a failed attempt that was undone): no entry; say so in one line.

If the project has no `loc/MEMORY.md`, ask as for any skill in a project without `loc/` (session start): `loc-init` first, or nothing and stop.

## 2. Write the entry

In English: a title of a few words, then **at most 3 sentences**: what was done and why, and what did not work out (a gate that ended in `stuck`, an open `question`). End with the source file: `Details: loc/inbox/done/NNN-<type>-<topic>.md`. Facts only: no praise, no plans for later.

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type <Plan|Planning|Review|Fix|Decision> --title "<title>" --text "<sentences> Details: <file>"
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

The script adds the entry with the current time, sorts newest first, regenerates the index between the markers and trims to the newest 1000 entries. Never write the entry, the time or the index by hand.

## 3. Tidy `loc/PATTERNS.md`

New lessons go into `PATTERNS.md` at the moment they are learned (rule 10), not here. Here only check what this work touched:

- An entry the work **contradicted** (a way that no longer works, a trap that is gone): correct that entry in place. Never add a second, conflicting one.
- A lesson from this work that the code cannot tell and that is **not yet recorded**: add it, at most one, only if losing it would cost someone time again. It gets a **When to use** line, so planning and review find it with grep, and goes under ✅ Works, ❌ Does not work or ⚠️ Pitfalls.

Nothing to change is the usual result.

## 4. Report

One or two lines in the user's language: the entry's heading, and what changed in `PATTERNS.md`, if anything.
