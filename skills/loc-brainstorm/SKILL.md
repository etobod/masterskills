---
name: loc-brainstorm
description: Use as soon as a conversation turns into shaping a change (ideas for a feature, options being weighed, "thinking about…", "what if…", a decision about how something should work) and nobody has asked for a plan yet. Keeps one growing brainstorm file in loc/inbox/ with numbered decisions. Also when the user asks to note or continue a brainstorm.
argument-hint: "[topic]"
---

# loc-brainstorm

Keeps the notes of a design conversation in **one** file, `loc/inbox/NNN-brainstorm-<topic>.md`, so the conversation survives `/clear`, compaction and the next session, and so `loc-planning` can turn it into a plan.

Brainstorming only records. **Do not write code, do not write a plan**, even when the idea looks finished. The user moves on with `loc-planning`.

## 1. Find the active file

Look for `loc/inbox/*-brainstorm-*.md` (not `loc/inbox/done/`).

- **One exists**: continue it, even if the topic drifted. Add a `### <new topic>` subheading under `## Notes` when it did.
- **Several exist**: continue the one about this topic; if none is, the most recent.
- **None exists, or the user explicitly asks for a separate one**: create it with the script. Never pick the number yourself.

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type brainstorm --slug "<topic, few words>" --title "<topic>" --source "conversation" --by loc-brainstorm
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

It prints JSON with `path`; the file already has the header and sections. Write it in English, like everything in `loc/`.

## 2. Write in the same reply

Every reply in which something new was said updates the file **before** you answer. Content:

- **`## Topic`**: what the conversation is about, one paragraph. Keep it current.
- **`## Notes`**: what the user said and what you found (facts from the code with `file:line`). Append; no length limit. Record substance, not a transcript.
- **`## Decisions`**: each decision the user made, numbered `B-01`, `B-02`… in order, one line each with the reason. Numbers are never reused. A decision the user changes is struck through (`~~B-02 …~~ → replaced by B-04`) and the new one gets the next number, so plans can refer to them safely.
- **`## Open`**: what is still undecided, each with your recommendation when you have one. Remove an item when it becomes a decision.

Record only what the user decided as a decision. Your suggestion stays in `## Open` until they agree.

## 3. Answer

Answer the user normally: discuss, weigh the options, ask what is needed. End with one line naming the file, e.g. "Notes: `loc/inbox/004-brainstorm-greeting-language.md` (B-01…B-03)."

When the open list is empty or the user says the idea is ready, mention that `/masterskills:loc-planning <NNN>` makes a plan from it. When `## Goal` in `loc/PRD.md` is still only the template, mention first that `/masterskills:loc-init <NNN>` fills the project's goal and `CLAUDE.md` from it. Do not start either yourself.

## Rules

- One active brainstorm; a second only when the user asks.
- The file must make sense on its own to someone who missed the conversation.
- The brainstorm is closed by `loc-planning`, never by this skill.
