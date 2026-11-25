---
name: loc-orchestrate
description: Use when the user asks to execute a plan from loc/inbox/ (e.g. "loc-orchestrate 018", "execute plan 018"), or to resume one that has a state file in loc/state/. Checks the plan, starts the orchestrator agent that builds it milestone by milestone with a proof per milestone and one review of the whole plan, and asks the user its questions in one round.
argument-hint: "<plan number or file>"
---

# loc-orchestrate

Starts the `orchestrator` agent on `loc/inbox/NNN-plan-<topic>.md`. The agent builds the plan; this session only checks that it may start, asks the user what the agent could not decide, and reports. The main session's context then holds the start, the questions and the report, never the plan's work.

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

## 1. Start

1. `$ARGUMENTS` is a plan number or file in `loc/inbox/`. No argument: if `loc/state/` holds a file whose `phase` is not `done`, resume it; otherwise the first plan in `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/plan_queue.py` not `blocked`; no open plan: say so.
2. If `loc/state/<NNN>.json` exists, this is a **resume**: validate it (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_state.py loc/state/<NNN>.json`, exit `0` or fix it). `phase` `done`: the plan is finished, say so and stop. Otherwise, with `questions` left go to §3, else to step 4, then §2.
3. The frame: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/frame.py`; not `ok`: `${CLAUDE_PLUGIN_ROOT}/skills/loc-init/references/frame.md` first.
4. Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/check_plan.py --ready <plan>`. If it exits non-zero, the plan's status says the gate failed, or `loc/inbox/` has an open `PRD:` `question`, **stop**: say why, point to `/masterskills:loc-planning`; no architect, no edits to the plan.
5. Create the state file with `"mode": "agent"` (`references/state.md`, Start value).
6. Copy the tests: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/test_baseline.py --plan <NNN>`.

## 2. Run the agent

Start it, and wait for its report:

```
Agent(subagent_type: "masterskills:orchestrator", prompt: "Plan: <plan path>
State: loc/state/<NNN>.json
Procedure: ${CLAUDE_PLUGIN_ROOT}/skills/loc-orchestrate/references/run.md")
```

Its report starts with `Status:` and ends with `End of report.` A lost report (empty, no end line) is asked for again from the same agent, up to 3 times (core rule 6a); still lost: stop and tell the user the run is lost at the state file's `next_action`, never start a second orchestrator on it.

- `Status: done` → §4.
- `Status: waiting: questions` → §3.
- `Status: stopped: …` → tell the user what is missing in one line; the run resumes from the state file once it is given.

Do not do the plan's work here, and do not read its diffs: the state file and the report are the whole record.

## 3. Questions

The state file's `questions` lists each matter, `{"file", "ask"}`. Read each file and ask every matter in one `AskUserQuestion` round: a `question` file's `### ` choices with their options, the recommended option first, named by file, letter and content (`088 A: finish the entry`); the checks sheet (`NNN-U-checks.html`): its path, and ask for the ratings by number ("3 ok, 5 fix: …").

Record each answer as core rule 8 says: under `## Resolution` and the file moved to `loc/inbox/done/`, a rating with `checks.py --rate`, an answer other than the interim option also as a `deferred` file. Then set `questions` to `[]` and `next_action` to what follows the answers, and go back to §2: the agent resumes from the state file.

In a `loc-director` course the director goes on after the answers: never ask to continue.

## 4. Report

The agent's report, in the user's language and briefly: the commit, milestones with proof results, gates that went stuck, deviations, new inbox files, the checks sheet with its open points, QA verdict, final review result, the cost line. Then **"Judge: enough"**: its numbered `enough` lines, grouped by PRD point; "fix 2" goes to `loc-planning`. Questions the agent left at the end (`questions` not empty) are asked first, in one round, and recorded as in §3, then `questions` set to `[]`; the plan is done, so never back to §2.
