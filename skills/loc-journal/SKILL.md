---
name: loc-journal
description: Use after work that changed something, to record it in docs/MEMORY.md — called by loc-orchestrate when a plan ends, and after a review, a fix outside any plan or an important decision (e.g. "loc-journal", "zapisz w dzienniku"). Also tidies contradicting entries in docs/PATTERNS.md.
argument-hint: "[inbox/done file | what was done]"
---

# loc-journal

Keeps the project's diary, `docs/MEMORY.md`: what was done, newest first, one short entry per piece of work, so anyone can find it again by topic and date. The diary records history; the code stays the truth about the present.

**Do not touch `docs/PRD.md`. Do not commit.**

## 1. What to record

`$ARGUMENTS` is an `inbox/done/` file (a plan, a review, a question) or a description of the work. No argument: take the work just finished in this session. One entry per piece of work, of one type:

| Type | When |
|---|---|
| `Plan` | a plan was executed (`loc-orchestrate` calls this at the end) |
| `Przegląd` | a review was done (`loc-review` on its own) |
| `Poprawka` | a change outside any plan that actually changed something |
| `Decyzja` | an important decision, e.g. an answered `pytanie` that changes direction |

Nothing changed (a conversation, a question, a failed attempt that was undone): no entry; say so in one line.

If the project has no `docs/MEMORY.md`, say that `/masterskills:loc-init` creates it, and stop.

## 2. Write the entry

In Polish: a title of a few words, then **at most 3 sentences**: what was done and why, and what did not work out (a gate that ended in `utknelo`, an open `pytanie`). End with the source file: `Szczegóły: inbox/done/NNN-<type>-<topic>.md`. Facts only: no praise, no plans for later.

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/memory_index.py --type <Plan|Przegląd|Poprawka|Decyzja> --title "<title>" --text "<sentences> Szczegóły: <file>"
```

The script adds the entry with the current time, sorts newest first, regenerates the index between the markers and trims to the newest 1000 entries. Never write the entry, the time or the index by hand.

## 3. Tidy `docs/PATTERNS.md`

New lessons go into `PATTERNS.md` at the moment they are learned (rule 10), not here. Here only check what this work touched:

- An entry the work **contradicted** (a way that no longer works, a trap that is gone): correct that entry in place. Never add a second, conflicting one.
- A lesson from this work that the code cannot tell and that is **not yet recorded**: add it, at most one, only if losing it would cost someone time again. It gets a **Kiedy stosować** line, so planning and review find it with grep, and goes under ✅ Działa, ❌ Nie działa or ⚠️ Pułapki.

Nothing to change is the usual result.

## 4. Report

One or two lines in the user's language: the entry's heading, and what changed in `PATTERNS.md`, if anything.
