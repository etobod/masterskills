---
name: loc-director
description: Use when the user wants the work run for them ("loc-director", "work until plan 087 is done", "work until 21:00", "carry on without me"), asks what the director did ("loc-director status"), or stops it ("stop"). Agrees a course once, then plans and executes it with pm and architect, and stops only on its stop rules.
argument-hint: "[status | stop | <what to work on and until when>]"
---

# loc-director

You run an agreed course so the user does not work out the next step from three voices. Roles are fixed: the `architect` agent says **what** a matter needs, the `pm` agent says **in which order**, you only **execute** and check the stop rules. You add no opinion of your own and **never invent work**: no new goal, feature or improvement. Every item comes from an agreed plan or an inbox file, and names it.

The course lives in `loc/PRD.md` `## Course`; only `course.py` changes it. Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`.

## Arguments

- **`status`** (or the user asks in words while you work): run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py status --mark` and show its output as it is. Then carry on.
- **`stop`** (or the user says "stop"): `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py stop --reason "the user said stop"`, then the stop report.
- **Anything else**: with an open course, resume from its `**Next:**`; without one, agree a course.

## 1. Agree the course

1. Read every open file in `loc/inbox/` without exception, and `loc/PRD.md`.
2. In one step, call the `pm` agent (order of the plans and of the `deferred`, `stuck` and `review` files) and the `architect` agent in Triage mode (what each `stuck`, `deferred` and `review` file needs: a plan, a decision, nothing).
3. Show a table in the user's language: item, source file, what follows (`loc-planning`, `loc-orchestrate`, waits for you), in the pm's order. Files with `U` wait for the user and are not items.
4. The limit, from the user's words:

| User says | `--limit` | Which files you take |
|---|---|---|
| nothing, or "until plan 087 is done" | `goal` | the agreed items and what they produce (a file whose `**Source:**` names one) |
| "until I say stop" | `none` | also older files, after the agreed items |
| "until 21:00" | `until <YYYY-MM-DD HH:MM>` | as `none`; the Stop hook checks the clock |

5. When the user agrees: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py start --limit <limit> --agreed "<their words>" --item "plan 084" --item "loc/inbox/091-stuck-x.md"`. One question at a time until then; never start without the agreement.

## 2. Run it

Repeat, never asking "should I continue?":

1. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py next --text "<the step, e.g. loc-orchestrate 084>"` **before** starting it, so a cut run resumes there.
2. Run it: `Skill(skill: "masterskills:loc-planning", args: "<NNN>")` for an inbox file or an agreed plan without one, `Skill(skill: "masterskills:loc-orchestrate", args: "<NNN>")` for a plan. A failed plan gate, a stuck gate or a question inside them is handled there.
3. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py done --item "<item>"`.
4. New inbox files: the architect says what each needs; within the limit, `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py add --item "<item>" --source "<file> (<the plan that made it>)"`; the pm orders the open items.
5. Read any message the user typed, and check the stop rules.

The architect's word is followed. Its ruling goes where it applies, marked `(architect, <date>)`; a matter beyond its competence becomes a `question` with `U` and waits.

## 3. Stop rules

Stop only when:

- every item is done (with `goal`, also what they produced, within the limit);
- what is left waits for the user (`U` files), and nothing else can go on;
- the same stuck point comes back after a plan made for it: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/inbox_owner.py --number <NNN> --user` instead of a third plan, then go on with the rest;
- the Stop hook says the time limit or the step cap is reached; a running task is finished first.

Then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/course.py stop --reason "<which rule>"` and the stop report.

## 4. Stop report

In the user's language, briefly:

```
Done: plan 084 (commit a1b2c3d), plan 091 from stuck 091.
Skipped: loc/inbox/080-deferred-old.md — outside the goal of this course.
Left: loc/inbox/092-U-question-cache.md waits for you (092 A: one cache module, recommended).
Resume: /masterskills:loc-director
```

Name every option by its file, letter and content. The resume command comes last, also when nothing is left.
