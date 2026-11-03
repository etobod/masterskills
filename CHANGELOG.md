# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

## 2.25.0 — 2026-11-03

- Search milestones (`**Kind:** search`): a milestone that improves a number toward a target (a pass rate, a speed) within a budget of iterations, 50 by default, more only with the user's consent. Missing the target is accepted, never a stuck gate. Every other milestone is a proof milestone, as before.
- `loc-planning` picks the kind by one test: a search only when the requirement is a number to improve or the user asked for one, never as a way out of a hard proof. The plan sets the metric, target, stop rule, how a result is measured, a hold-out set and leads from the `researcher`; `check_plan.py` checks those fields.
- `loc-orchestrate` runs the loop from `references/search.md`: a fresh `searcher` agent per try, the new `search_log.py` decides keep, revert and stop and keeps the log a resumed run continues from. Only a better result is committed; the search stops at the target, never past it. A metric change needs the `judge`, at most two. The summary gives the start and best score, the stop reason and how it could go further, also as a `deferred` file.
- `rubber-duck` judges only a search's preparation and checks the kind both ways; `judge` keeps review fixes away from the metric, cases, hold-out and guard. `check_state.py` knows the `search` phase and the `M<n>/search` gate.
- Budgets raised: `loc-planning` `SKILL.md` 2720 words, `loc-orchestrate` `SKILL.md` 1350.

## 2.24.2 — 2026-11-03

- OpenCode build: `date "+%Y-%m-%d"` in the skills becomes a Python one-liner, since OpenCode on Windows runs commands in PowerShell, where `date` fails and every dated step cost a retry.

## 2.24.1 — 2026-11-03

- OpenCode build: an agent gets only the tools its `tools:` line lists, as in Claude Code. Everything else is denied (`"*": deny`), so a reviewer no longer fetches web pages or calls MCP servers; the plugin's own files stay readable.

## 2.24.0 — 2026-11-03

- `loc-review` and `loc-orchestrate`: each reviewer (`rubber-duck`, `code-review`) runs once per round; an empty or unreadable answer counts as no findings, never a relaunch. A model that could not read a long answer started the same reviewer three times.
- `loc-review`, orchestrated: the final `code-review` looks only at how the milestones work together and at what changed after the last milestone's `end`, since each milestone's diff was already reviewed at its own gate. The final `rubber-duck` still reads the whole plan.
- Every agent ends with its report alone: it checks in silence, never lists what passed, and with nothing to report says so in one line. A reviewer that narrated every criterion ran out before its report and came back empty.
- Agent budget raised by 100 words: 600 per agent, 650 for `rubber-duck` and `judge`.

## 2.23.1 — 2026-11-01

- `loc-planning`: a file a proof, test or manual check needs is kept in git or made by the test, never added to `.gitignore`. A plan that ignored its own sample input failed on any clean checkout.

## 2.23.0 — 2026-11-01

- `loc-init` in Claude Code on Windows also leaves `open-code.bat` when the OpenCode build of masterskills is installed on the machine (its `SOURCE` file in the OpenCode config names a repository with `opencode-install.bat`). Without it only `claude.bat` is created, as before; an existing launcher is never touched.

## 2.22.0 — 2026-11-01

- New skill `loc-debug` for a reported bug outside a plan: reproduce it with one command, pin it with a test that fails on it, test two or three hypotheses cheapest first, fix the cause and not the symptom. At most 3 rounds of hypotheses; a fix too large for one change, or a cause not found, becomes a `deferred` file with the reproduction and the test.
- Frontend projects: a new `## Frontend` section in `CLAUDE.md` names the design plugin installed beside masterskills, its review command, a UI check command that fails on a defect, and the screenshot command with its widths. With it filled, brainstorms record a visual direction for every new screen, plans run the UI check in the proof of every milestone that changes what the user sees, and `loc-review` runs the design review beside the other reviewers (source `[design]`). `loc-init` adds the section to existing projects; the `loc/TEST-PLAN.md` example has `ui` and `screenshots` layers.
- Every review finding gets a verdict before the judge: `confirmed`, `needs_validation` or `rejected`. An unconfirmed finding goes to the judge marked as such instead of being dropped; a rejected one is dropped with one line saying why. The gate keeps the last round's counts in `verdicts`, checked by `check_state.py`.
- Before writing code, `loc-orchestrate` checks whether it needs to exist: already in the project, the standard library, the platform or an installed dependency. Validation, error handling, security and accessibility are never cut. Code review also flags new code that duplicates what is already there.
- `loc-brainstorm` has a grill mode ("grill me"): it asks one question at a time about the weakest point of the idea, each with a recommended answer.
- `loc-diagram` marks every box and arrow as read from the code (`file:line`) or inferred (`?`).

## 2.21.1 — 2026-10-31

- README rewritten for a public repository: what the plugin does, the team of agents, the skills, and how it compares with other skill packs.
- MIT `LICENSE` file.
- Tests and scenarios no longer name a local drive: test projects go to `../tmp/masterskills/` beside the repository.

## 2.21.0 — 2026-10-31

- `loc-init` in a directory without git asks with a choice prompt: run `git init` (recommended) and go on, or no and stop as before.
- `loc-init` in a new project without a brainstorm opens a project brainstorm right after creating the files: what the user writes about the project goes there. When the notes say what the project is for, the points it stands on and how it is used, `loc-brainstorm` offers to fill the project from it (`loc-init <NNN>`) or keep talking.
- Filling the project from a brainstorm marks each decision and note it used `→ moved to <file> <section>`; what is left is the work `loc-planning` makes a plan from.
- In a project without `loc/`, a masterskills skill first asks: run `loc-init` first (recommended), then the skill, or do nothing, and the skill does not run.

## 2.20.0 — 2026-10-31

- New skill `loc-diagram`: a question like "how does saving an entry work?" gets a diagram drawn in the terminal from the code read now, with `file:line` on every box, a numbered walk-through, what is left out and where to look first.
- Diagrams are kept in `loc/diagrams/`, one file per topic, each with the commit it shows. Asked again, an unchanged diagram is shown at once and a changed one is redrawn in the same file. The project overview and the topics listed under the new `## Diagrams` section of `CLAUDE.md` stay; every other diagram goes to `loc/diagrams/tmp/`. "Keep it" moves one out of `tmp/`.
- The overview and every kept diagram also get a self-contained HTML version (inline SVG, light and dark) to open in the browser; any other diagram gets one on request.
- `loc-orchestrate` refreshes the overview after every plan; it redraws it only when the plan added, removed or renamed a part of the project or a flow between parts.
- `loc-init` creates `loc/diagrams/` and `loc/diagrams/tmp/` and adds the `## Diagrams` section.
- A new plugin version draws the overview: the overview records the version it was drawn with (`**Plugin:**`), and at session start a project without it, or with another version, is asked to draw it before other work.

## 2.19.0 — 2026-10-31

- When work waits on a `question` file (a `PRD:` change, a blocker only the user can remove, what a director's stop report leaves), the user also gets Claude Code's choice prompt (`AskUserQuestion`): one line naming the file, its options with the recommended one first, and their own text as another answer. The file stays the record; the answer goes under `## Resolution` as before. A question the work goes on without stays a file only, so a director's night run does not wait on a click.
- `loc-planning` asks for consent to a `PRD:` change with the prompt.
- OpenCode: `AskUserQuestion` becomes its `question` tool.
- Core rules trimmed to stay within 470 words.

## 2.18.7 — 2026-10-24

- `loc-orchestrate`: a blocker only the user can remove (e.g. a file outside the project is gone) gets a `question` file at once, never only in chat; the milestone goes `stuck` and the next one starts. Before, the question stayed in chat and, under the director, every stop of the turn repeated "waiting for your answer".

## 2.18.6 — 2026-10-22

- A change to `Goal`, `Core idea` or `Scenarios` is asked in a `PRD:` `question` file (`NNN-U-question-…`) also outside a plan, never only in chat. A yes/no asked only in chat was lost when the next agent report pushed it out of view.
- Rule 3: only a quick clarification stays in chat; a question the user may miss never does. Rules trimmed to stay within 470 words.

## 2.18.5 — 2026-10-22

- `loc-director` never starts a course without showing its table first. When the `pm` and `architect` answered after the director's reply had ended, it could go straight to `course.py start` and show only the banner.

## 2.18.4 — 2026-10-22

- A director's step is one executed plan: `course.py next` counts a new `loc-orchestrate <NNN>`, once per plan, also when it is resumed. Planning, inbox files and agents' answers no longer count; before, every stop of the turn (2.18.1) or every `next` (2.18.3) did. The cap is the agreed items + 10 (20 in the table → 30; none → 10); the user can name another (`--cap`).
- At each new step the user sees a line like `-------- ended: loc-planning 084 | starting: loc-orchestrate 084 | plans 3 of 10 --------`. `course.py next` prints it as `banner` and `loc-director` shows it as it is, so it is easy to tell where one task ends and the next begins. The Stop hook names the plans executed too.

## 2.18.3 — 2026-10-22

- The director's step cap counted every stop of the turn, so waiting for a background agent used it up ("step 15 … 19 of 40" with the same next step). Now `course.py next` counts a step, when work starts. The `Stop` hook no longer counts, and when it already made the model go on (`stop_hook_active`) and the model stops again, it lets the turn end: the model is waiting, and the agent's result resumes it. The time limit is still checked at every stop.

## 2.18.2 — 2026-10-22

- A plan that changed only `loc/` (e.g. `loc/TEST-PLAN.md`) has nothing for the final review: `review_diff.py` leaves `loc/` out. `loc-review` now says what goes into the state file then, `final-review` with `rounds: 0, passed: true`, so the model no longer improvises it.

## 2.18.1 — 2026-10-22

- `loc-director` no longer asks "agreed?": calling it is the agreement, with words ("work without limits", "until 21:00", "finish plan 087") or without (limit `goal`). It shows the table and starts in the same reply; it asks only for work the table cannot cover. "Without limits" means `--limit none`; `/masterskills:loc-director status` only looks.

## 2.18.0 — 2026-10-22

- New skill `loc-director`: you agree a course once ("until plan 087 is done", "until I say stop", "until 21:00") and it runs it. The `pm` agent orders the plans and the `deferred`, `stuck` and `review` files, the `architect` agent says what each needs, and the director plans and executes until a stop rule: all done, only your files left, the same stuck point back after a plan for it, or the time or step limit. It never invents work and never asks whether to continue; every stop ends with Done / Skipped / Left and the resume command. The course lives in `loc/PRD.md` `## Course` (`scripts/course.py`); a `Stop` hook keeps it going and checks the clock; `/masterskills:loc-director status` prints what happened since the last report.
- The user gets only what the architect cannot decide. Where a skill would ask a question, it first calls the `architect` agent in a new Decide mode: within its competence (technical choices inside Goal, Core idea, Scenarios, Decisions and Invariants) its ruling `<what> — <why> — cost if wrong: <…> (architect, <date>)` is applied at once; beyond it a `question` file is created. Triage asks only beyond that competence.
- An inbox file that waits for you has `U` after its number (`088-U-question-…`): questions, an open brainstorm, and a file handed to you with `scripts/inbox_owner.py --user`. Session start lists them first. Lookups go by number, so a renamed file is still found.
- A brainstorm is `**Status:** open` while discussed and `approved <date>` once you say to go with it.
- Options are named by file, letter and content (`088 A: finish the half-written entry`); "as the architect recommends" is an answer. The architect names its options by word and ends with `Bears on: 088 → A`.
- A milestone or QA gate stuck after 3 rounds writes no `stuck` file: its record goes into the plan's `## Stuck gates`, and the architect weighs it once at the end, also when the final review passed. A failed plan gate gets the architect's Triage. A `review` file waits for the director, not for you.

## 2.17.0 — 2026-10-21

- A decision the model asks the user for becomes a `question` file in `loc/inbox/`, in a skill or not (core rule 3); a quick clarification stays in chat. Before, outside a skill such a question stayed only in the conversation.
- `check_plan.py` fails a plan that names a `D-NN` absent from `loc/PRD.md` (and from its own `## PRD fragment`) unless it points to the `NNN-question-…` file that asks the user about it, so a proposed decision never lives only in a planning report.
- `commit_plan.py` no longer commits a new top-level directory git tracks nothing in, such as `data/` written during a manual check. It stops and names the directory; `--add <dir>` commits it as the plan's work, `--leave <dir>` leaves it on disk (listed in `left`), and `loc-orchestrate` then asks in a `question` file whether it goes into `.gitignore`.

## 2.16.0 — 2026-10-21

- A `stuck` file shows at once which gate stuck and what the architect recommends. `**Source:**` names the gate before the plan (`M1 code-review (milestone) of <plan path>`), and a new header line `**Stuck gates:**` lists every gate in the file. Each gate section opens with `**Gate:**`, `**Architect (Challenge):**` or `**Architect (Triage):**` (its verdict and recommendation) and `**Next:**` (what happens to what remains), then `### What remains`, and only then the rounds.

## 2.15.0 — 2026-10-21

- Every inbox file names its author, not only a question. `next_number.py` requires `--by` for every `--type` and creates no file without it. A question gets `**Recommended by:**` (who weighed its options); a `brainstorm`, `plan`, `deferred`, `review` or `stuck` file gets `**Created by:**`, e.g. `loc-orchestrate`. Every skill and hook that creates an inbox file passes it.

## 2.14.0 — 2026-10-21

- A `question` file says who weighed its options: a new header line `**Recommended by:**`, e.g. `architect (Triage)`, `loc-planning` or `loc-orchestrate`. `next_number.py --type question` requires `--by` and creates no file without it. Every place that creates a question passes it; when the architect weighed the options and the orchestrator only writes the file, the architect is named.

## 2.13.0 — 2026-10-21

- A final review stuck after 3 rounds no longer just closes the plan. `loc-orchestrate` calls the `architect` agent in a new Triage mode, which picks one: **retry** (rounds 4–6, once per plan), **plan** (the remaining points go to a `deferred` file for `loc-planning`) or **ask** (a `question` file for the user: what is at stake, the options, the recommended one first). After round 6 only `plan` or `ask`. `check_state.py` enforces it through the gate's `triage` list.

## 2.12.2 — 2026-10-20

- `claude.bat` made by `loc-init` ran `claude`, which in the project directory is `claude.bat` itself, so it called itself and failed with "The syntax of the command is incorrect.". It now runs `claude.exe`. `init_project.py` rewrites a launcher in the old form, keeping its session id; a launcher written by the user is left alone.

## 2.12.1 — 2026-10-20

- `loc-planning` no longer proposes a decision only in its report, where it is easy to miss: every decision the user has not approved yet goes into one `question` file (`Decision: <topic>`) with ready `D-NN` lines and their practical effect. After the answer the approved lines are written to `loc/PRD.md` `## Decisions`.

## 2.12.0 — 2026-10-19

- New `pm` agent, read-only, with a clean context: after every new plan it orders the whole queue of open plans, so a plan is not first only because it was just written. It reads `## Goal`, `## Core idea`, `## Decisions` and the new `## Priorities` of `loc/PRD.md`, keeps a running plan first, never puts plans with shared files in one group, and gives group 1 before the waiting plans only when the user called a plan urgent. It returns a reason per plan and the command to apply.
- `loc/PRD.md` has a `## Priorities` section written only by the user: what matters most now, which the `pm` follows over its own view.
- `plan_queue.py --set NNN=G` (repeatable) gives plans their groups, renames the files and fixes every reference under `loc/`; a running plan is skipped. `loc-planning` creates a plan at the end of the queue and runs the `pm`'s command after the gate.
- `loc/` format 4: `migrate.py` adds `## Priorities`. An open plan written before groups, not running, that fails the plan check on its own text becomes a deferred item (`NNN-deferred-<topic>.md`, `**Type:** deferred` and a `**Deferred:**` line with the reason; the rest of its text untouched), to be planned again. `loc-init` reports these and asks the `pm` to order the remaining plans.

## 2.11.0 — 2026-10-18

- `loc/PRD.md` has a `## Decisions` section: lasting choices later plans follow, one line each, `- D-NN: <decision>. Reason: <why>. (<date>)`. Plans cite `D-NN` instead of restating it. A replaced decision leaves the PRD (into the plan's `## PRD fragment`) and its successor says `replaces D-NN: <why>`. `loc-planning` adds one after the user agrees; the rubber-duck treats a plan that silently contradicts a decision as blocking.
- New `architect` agent, read-only, with a clean context. Harvest mode proposes decisions from finished plans and lists choices the plans reversed back and forth. Challenge mode weighs whether a decision still serves the project's goal: called when the judge answers `challenges D-NN`, after a stuck gate, or on the user's request. Its report becomes a `question` file; the user decides.
- The judge reads `## Decisions`: a decision not followed is `fix`; a finding against a decision with an argument its `Reason` already weighed is `enough [D-NN]`; one with a new argument is `challenges D-NN`, recorded as `enough` while the decision holds.
- `loc/` format 3: `migrate.py` adds the empty section to an existing PRD (run by `loc-init`, which the session start asks for). When the project has finished plans and no decisions, `loc-init` asks the architect to harvest them into one `question`; nothing enters the PRD before the user approves.

## 2.10.0 — 2026-10-18

- One queue for all open plans: every plan name carries its group, `NNN-plan-<group>-<difficulty>-<topic>.md`. A lower group runs first; plans of one group change different files. A series is no longer a separate idea: several plans from one input are plans in the queue.
- New `scripts/plan_queue.py` prints the queue (plans without a group, written before this release, come first). `--make-room G --keep NNN` raises by one the group of every open plan from G up, except the new plan and the one being executed, renames the files and fixes every reference to them under `loc/`.
- `loc-planning` picks the group: the highest in the queue when the plan changes no file its plans change, else the next one; an urgent plan takes group 1 and, when it must go before a group 1 plan, makes room. `loc-orchestrate` without an argument takes the first plan in the queue.
- `check_plan.py` requires the group in the planning gate; with `--ready` old names still run.

## 2.9.0 — 2026-10-18

- New core rule 13, tests with the user: a short overview, then one step per message (`Step 1/N`, what to install or open, the exact text to type, "paste the reply"); the model checks files itself. It applies in every project, also outside a skill.
- To fit the rules budget, rules 2, 3 and 11 are shorter; the sentence that a finding the judge did not mark `fix` is not deferred work left the core rules (`gates.md` and `loc-planning` already say it).

## 2.8.1 — 2026-10-18

- When the model tells the user about a judge round (a milestone's code review, the final review), it lists every finding the judge saw: the `fix` ones, then each `enough` with the judge's reason in one sentence. Before, the message said only how many findings were judged `enough`.

## 2.8.0 — 2026-10-18

- A plan keeps to a milestone limit set by its difficulty: `easy` 6, `medium` 4, `hard` 3. An M1 that sets up the test suite is not counted. `check_plan.py` enforces it in the planning gate (not with `--ready`, so older plans still run); over the limit, `loc-planning` splits the work into a series, also when the user did not ask for one.
- The difficulty describes the kind of change, not the number of milestones: `easy` means each milestone is a local change to existing code. The plan's critic is also asked whether a milestone does several independent things, so plans do not merge milestones to fit the limit.

## 2.7.0 — 2026-10-18

- Plan names carry the difficulty: `NNN-plan-<easy|medium|hard>-<topic>.md`, so the user sees at a glance which model can run a plan. `loc-planning` gives the criteria (`easy`: one or two milestones, no new file, interface or data model; `hard`: a new component, a changed interface or data model, or a risky change to widely used code; otherwise `medium`).
- A series (several plans from one input, when the user asks for it) adds an execution group: `NNN-plan-<group>-<difficulty>-<topic>.md`. Lower groups run first; plans sharing a group are independent.
- `check_plan.py` rejects a plan name without the difficulty in the planning gate. With `--ready` (the start of `loc-orchestrate`) the name is not checked, so plans written before this release still run.

## 2.6.0 — 2026-10-17

- New PostToolUse hook `state_check.py`: after every `Write`/`Edit` of `loc/state/<NNN>.json` it runs the `check_state.py` checks and gives the model the problems, or nothing when the file is valid. `loc-orchestrate` no longer runs the validation command after each state update (only once when resuming a run), which saves a tool call per update.
- OpenCode: the plugin bridge runs PostToolUse hooks after `write`, `edit` and `apply_patch` too, not only after `bash`.
- `check_state.py`: `mode: inline` is for 2 milestones at most; a larger plan run inline needs a rule-3 deviation saying why. A run already in progress that breaks this gets the message at its next state write.

## 2.5.3 — 2026-10-17

- `opencode-install.bat` first upgrades OpenCode itself (`winget upgrade --id SST.opencode -e`, no prompts). Every `open-code.bat` made by `loc-init` calls it, so starting OpenCode from a project also keeps OpenCode current. No `winget`, no newer version or a failed upgrade does not stop the plugin install.

## 2.5.2 — 2026-10-17

- OpenCode: the milestone and final review gates had no `code-review`, which is a skill built into Claude Code, so a model substituted `rubber-duck`, which does not look for bugs. The OpenCode build now installs a `code-review` agent (`opencode/agents/code-review.md`: correctness findings with `file:line` and `high`/`medium`/`low`, read-only) and turns each `Skill(skill: "code-review", args: "…")` into `task(subagent_type: "code-review", prompt: "…")`. `measure.py` counts `opencode/agents/*.md` against the agent budget. Claude Code is unchanged.

## 2.5.1 — 2026-10-17

- The `## Resolution` placeholder of a `deferred` file says what to do with the result of a manual check: each point passed or failed in the user's words; a failed point becomes a new `deferred` file or a plan, not a fix in the conversation unless the user asks; its fix starts with a test that fails on it. Only new `deferred` files get it.

## 2.5.0 — 2026-10-17

- `next_number.py --what --why --when` fill the sections of a `deferred` file in the command that creates it; `loc-qa` and `loc-orchestrate` use them, so a deferred manual check is never left as the empty template.
- The inbox list at session start marks a file that still holds its template's first placeholder: "still the empty template: fill it or delete it" (`inbox_summary.py` field `template`).

## 2.4.0 — 2026-10-16

- `loc-init` leaves a launcher on Windows for the tool that ran it, and never touches an existing one. Claude Code: `claude.bat` resumes the session in which `loc-init` ran (`--session "${CLAUDE_SESSION_ID}"`). OpenCode: `open-code.bat` runs `opencode-install.bat` from the repository the plugin was built from (recorded by `opencode/build.py` in `masterskills/SOURCE`), then starts OpenCode.

## 2.3.1 — 2026-10-16

- When `loc/` is in an old format, the session-start hook also returns a `systemMessage`, so the terminal shows the user "run /masterskills:loc-init" even when the model does not pass on the request in its context.

## 2.3.0 — 2026-10-16

- **Tests run the real code.** New `scripts/test_copies.py` lists functions a test defines with the name and nearly the body of a function in the code (Python `def`, JavaScript `function` and arrow functions, also inside a page's `<script>`). Such a test passes whatever the code does. `loc-qa` (new step 4a) rewrites it to run the real code; a page's script is loaded with `readFileSync` and `vm`. A deliberate mock is INFO. `loc-planning` says a test never copies the code, and the `judge` marks such a finding `fix`.
- **Deferrable manual checks are not lost.** `loc-orchestrate` writes a `user (deferrable)` milestone's `**Manual check:**` into a `deferred` file once the proof and the review pass (planning no longer does, since no code existed then). `loc-qa` creates the file when it is missing.
- `loc-orchestrate`: a skipped step of the skill (the red gate, the `test-author` agent, a review) is not a deviation; do it, or the gate is stuck.
- Word budgets: `loc-planning` `SKILL.md` 2600, `loc-qa` `SKILL.md` 1000.

## 2.2.0 — 2026-10-16

- **The user checks after the model's tests, never instead of them.** A milestone that changes code has criteria with tests and a command proof also when a person must look at the result; `→ manual` criteria are allowed only next to criteria with tests. `check_plan.py` no longer exempts a `**Performer:** user (...)` milestone from criteria or from a command proof, and says why: "the user checks after your tests, not instead of them".
- `**Performer:** user (...)` and `**Manual check:** <what the user looks at>` go together; `check_plan.py` rejects one without the other. The plan template shows the pair as an optional comment.
- `loc-orchestrate`: a new step 6 asks the user for a `user (blocking)` manual check only after the proof and the code review passed. A fault the user reports first becomes a failing test, then the fix; the user is asked again only when that test passes.
- Older plans with only `→ manual` criteria no longer pass the gate; rerun `loc-planning` on them.

## 2.1.1 — 2026-10-16

- `check_plan.py`: the message about an expanded plugin path gives the exact path to write (`` write `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md` ``) instead of a general hint, which a model followed by replacing the wrong prefix.
- `check_plan.py`: a `${CLAUDE_PLUGIN_ROOT}/...` path in a plan must exist in the plugin; when a shorter tail exists, the message suggests it (`${CLAUDE_PLUGIN_ROOT}/masterskills/templates/...` → `${CLAUDE_PLUGIN_ROOT}/templates/...`). Paths with a placeholder (`<name>`, `*`) are not checked.

## 2.1.0 — 2026-10-16

- `loc-planning`: the judge is now a required, numbered step (3) in `SKILL.md`, before the plan is written. A model that read it in `references/findings.md` could decide that "the plan gate will check" and skip it. `findings.md`, `closing.md` and `tests.md` are merged into `SKILL.md`, since nearly every plan needs them; only `prd.md` stays a reference.
- `check_plan.py`: a plan whose `**Source:**` names a `review` accounts for every finding of it (`003 #2`, numbered in `## Findings` order). Blocking and Non-blocking ones go in a milestone (the judge's `fix`) or an `enough` line in `## Review notes`; Suggestion and Unrealistic ones only in `## Review notes`, never in a milestone; one already fixed may be noted under the review's `## Resolution`. The message names the `judge` agent.
- Word budgets: `loc-planning` `SKILL.md` 2400, `loc-orchestrate` `SKILL.md` 1200.
- The last Polish words without diacritics are gone from skills and scenarios (`tymczasowo wariant A`, `Przeniesione z loc/PRD.md`, `popraw N` → `fix N`); a test now catches them. `migrate.py` also translates `Przeniesione z loc/PRD.md`.

## 2.0.0 — 2026-10-16

- **Breaking: `loc/` is in English.** Headings, fields, statuses, inbox types and markers are English (`question`, `deferred`, `review`, `stuck`; `## Goal`, `**Proof:**`, `**Status:** open`…), and so is the text the skills write. Only the text of a `question` file is in the `User language` of `CLAUDE.md`, so a design question can be answered in the user's own language. Scripts, hooks, templates, skills, agents and scenarios use the new names; `loc/state/mutacja*` is now `mutation*` and `qa-historia.log` is `qa-history.log`.
- `loc/VERSION` holds the format of `loc/` (now `2`). `init_project.py` writes it into a new `loc/`.
- `scripts/migrate.py` brings an older `loc/` to the current format: it renames inbox files and state files, fixes every reference to them, translates every heading, field and marker, adds `## User language` (Polish) to `CLAUDE.md` and lists the files whose prose the model translates. Running it again changes nothing. `loc-init` runs it first.
- The session-start hook asks for `/masterskills:loc-init` when `loc/` is in an older format.
- `check_plan.py` also rejects vague English phrases ("to be confirmed", "maybe", "probably"…).
- Upgrading: run `/masterskills:loc-init` once in each project that already has `loc/`.

## 1.21.2 — 2026-10-16

- `check_plan.py`: a project has a test suite only when it has `loc/TEST-PLAN.md` **and** a test command (`test` or `spec`) in `CLAUDE.md` `## Commands`. Before, the file alone was enough, so a model told "M1 must set up the test suite" could write a stub `loc/TEST-PLAN.md` while planning and pass the gate with no tests at all. The message now says not to create the file while planning; `loc-planning` `references/tests.md` says the same.

## 1.21.1 — 2026-10-16

- `check_plan.py`: a proof with a command and `→` but its expected result written as prose now gets a message that quotes that result and shows the form, `` `<command>` → `<exact output>` ``. Before, one message mixed the format with the user-performer advice, and a model could spend a round guessing which applied.
- `check_plan.py`: a criterion must name a test, with `test` or `spec` in it (`test_app.py::test_polish`, `tests/fft.test.js::rms`, `TestParse`). A criterion pointing at a source file (`→ app.html`) used to pass the gate.

## 1.21.0 — 2026-10-16

- `loc/PATTERNS.md` gets entries at concrete moments. Rule 10: when a command or setup fails and another way works (another path, shell, tool or flag), record both before the next step, `✅` and `❌`. `loc-orchestrate` checks this before the journal entry, `loc-review` before its report. Before, the only trigger was "when you find a way that works", and projects ended up with nearly empty patterns.
- Word budgets: rules 470, `loc-orchestrate` `SKILL.md` 970.

## 1.20.1 — 2026-10-16

- OpenCode: script commands no longer need `sh`. On Windows OpenCode runs commands in PowerShell, so every `sh ".../py.sh" scripts/<name>.py` in a skill failed on the first try. The build now writes `<python> -B "<absolute path>/scripts/<name>.py"`, with the Python found at install time; the absolute path also stops a model from looking for the script under the skill's directory. The inbox and CI commands from the hooks follow the same form. Claude Code is unchanged.

## 1.20.0 — 2026-10-16

- `loc/PRD.md` has a new section `## Scenariusze`: 3–7 ways the project is used (who, what they do, what they expect to see). Like `Cel` and `Rdzeń idei`, it changes only with the user's consent. The `judge` reads it: a finding that breaks a scenario is `fix`, and an `enough` line may rest on `[Scenariusz <n>]`. Without scenarios the judge works as before.
- `loc-init` with a brainstorm fills `Scenariusze` from it. `init_project.py` reports a PRD frame section whose heading is missing (an older PRD) as empty.
- `loc-planning` starts with `init_project.py --check`. Empty PRD sections are proposed through a `PRD:` question, which holds `loc-orchestrate` until the user answers. Empty `CLAUDE.md` sections never stop planning: what the plan can establish goes into a milestone, the rest into the report. Sections that contradict each other become a question.
- Word budgets: `judge` 550, `loc-planning` `SKILL.md` 900.
- Upgrading: an existing PRD has no `## Scenariusze`. The next `loc-planning` proposes them and asks.

## 1.19.1 — 2026-10-16

- `loc-init` with a brainstorm ends with `init_project.py --check`, which writes nothing and lists the sections still empty and the `CLAUDE.md` sections written in Polish. A model that left the PRD's `Cel` empty, or wrote `Invariants` in Polish, now sees it. `Cel` is never left empty: the brainstorm's `## Temat` says what the project is.

## 1.19.0 — 2026-10-16

- `loc-orchestrate` commits each finished plan with the new `commit_plan.py`. The commit holds only the files the plan changed since its first snapshot, `loc/` left out, so the user's own uncommitted work stays as it was. The message must be Conventional Commits and must not mention AI. Nothing is pushed. A project whose `CLAUDE.md` says the user commits is skipped with a reason. `check_state.py` requires the result (`commit` in the state file) in the `done` phase.
- `review_diff.py --from HEAD` works in a repository with no commits: the whole project is the change. Before, a standalone `loc-review` stopped with `fatal: bad revision 'HEAD'`.
- Upgrading: a run resumed from an older state needs the commit step before `done`.

## 1.18.0 — 2026-10-16

Gaps a weaker model showed, now checked by scripts instead of only described in skills:

- `check_plan.py` rejects a criterion whose "test" is a shell check (`grep "salmon" page.html`, `test -f x.html`, `open x.html`, anything with `&&`, `|` or `;`). It also rejects an automatic proof that is not `` `<command>` → `<output>` `` or that only opens a file. A visual result needs the user as performer.
- `check_plan.py --ready`, run by `loc-orchestrate` at its start, also requires a round recorded in `## Bramka planu` and the plan's input file (brainstorm, review…) closed, so a plan whose `loc-planning` stopped before its gate or before closing the input does not run.
- `check_state.py`: a `done` milestone needs a passed `M<n>/code-review` gate and, with `**Kryteria:**`, a passed `M<n>/red` gate (or a deviation saying why). `journal` and `done` need a `final-review` gate. `done` needs the plan's status closed.
- `loc-planning` `references/tests.md`: how to test a project with no obvious framework (pure functions plus the language's built-in runner, visual checks by the user).
- Upgrading: a plan waiting in `loc/inbox/` with an empty `## Bramka planu` stops `loc-orchestrate`; run `loc-planning` on it. A run resumed from an older state may need its skipped code reviews done before the end.

## 1.17.0 — 2026-10-16

- A plan can no longer drop tests silently. `check_plan.py` rejects a milestone with neither `**Kryteria:**` nor `**Bez testów:** <reason>`, for example `**Bez testów:** tylko dokumenty`. It also rejects a plan with criteria for a project without `loc/TEST-PLAN.md` unless its M1 sets up the test suite. Exempt: a milestone that sets up the suite, and one the user performs.
- `loc-orchestrate` reports the `**Bez testów:**` milestones when it skips QA, instead of "no test suite".
- Plans written before 1.17.0 may now stop `loc-orchestrate` at its start. Run `loc-planning` on the plan to fix it. A plan already being executed is not checked again.

## 1.16.0 — 2026-10-16

- `loc-init` takes a brainstorm (`loc-init 001`, or a path to a `.md` file) and fills the project's frame from its decisions: `Cel` and `Rdzeń idei` in `loc/PRD.md` and the `CLAUDE.md` sections. Only sections that still hold the template are filled, and each point names its source (`B-03`). `Commands` gets only commands written in the brainstorm. Ideas and features stay in the brainstorm, which `loc-init` never changes, for `loc-planning`.
- `init_project.py` reports the empty sections in a new `empty` field.
- `loc-brainstorm` suggests `loc-init <NNN>` while the project has no goal yet.

## 1.15.2 — 2026-10-15

- OpenCode: every skill is a `/<name>` command again (`/loc-init`, `/loc-planning`…). OpenCode lists skills only in its `/skills` dialog, and the `opencode/slash` metadata the build used is not an OpenCode feature; the build now writes `commands/<name>.md`, which loads the skill and passes the arguments. `/loc-qa` runs in the `qa` agent as a subtask, as in Claude Code.

## 1.15.1 — 2026-10-15

- OpenCode: the core rules are appended to OpenCode's system message instead of being sent as a second one. Chat templates such as Qwen's in LM Studio reject any system message that is not the first (`System message must be at the beginning`). The end-to-end test now checks for a single system message.

## 1.15.0 — 2026-10-15

- **A new OpenCode project works after `/loc-init`.** The OpenCode install adds to the global `opencode.json`, only where missing: `"CLAUDE.md"` in `instructions`, because OpenCode reads a project's `CLAUDE.md` only when there is no `AGENTS.md` (which OpenCode's `/init` creates); and `permission.external_directory` `allow` for the plugin's own files, so skills read their references and templates without a prompt. A config that is not plain JSON, or a single `external_directory` value, is left alone and the install prints what to add by hand. `loc-init` itself needs no change.
- The plugin's `permission.ask` hook is gone; the config entry does that job and can be checked.

## 1.14.0 — 2026-10-15

- **Hooks in OpenCode.** The OpenCode build adds `plugins/masterskills.ts`, which runs the same Python hooks as Claude Code, chosen by the matchers in `hooks/hooks.json`: the write guard and the commit guard stop a tool with the hook's reason; the core rules and the open inbox go into the system prompt once per session and again after compaction; the CI check text is appended to the output of `git push`; every shell command sees `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PROJECT_DIR`; reading the plugin's own files needs no prompt. The install no longer adds the core rules to `instructions` in `opencode.json` and removes the entry 1.13.0 added, so the rules are not there twice.
- `tests/test_opencode_e2e.py` checks the hooks in a real OpenCode against a local stand-in model (`tests/fake_model.py`); nothing is sent outside the machine. It is skipped when `opencode` is not on PATH.

## 1.13.0 — 2026-10-15

- **OpenCode version.** `opencode/build.py` builds the plugin for OpenCode from the same files: skills become `/loc-*` commands, agents become subagents with `permission:` instead of `tools:`, `${CLAUDE_PLUGIN_ROOT}` becomes the absolute install path, and the core rules are added to `instructions` in `opencode.json`. `opencode-install.bat` installs and updates it (`git pull`, then a build into `~/.config/opencode/` that replaces only the files of the previous install). Hooks and `loc-init` for OpenCode come later.

## 1.12.0 — 2026-10-15

- **The judge weighs every `odlozone`.** `loc-planning` (`references/findings.md`) now sends every `odlozone` through the judge before planning: review findings, observations from a manual check and `fix` findings deferred earlier. An observation from a manual check has no category; it goes to the judge as Non-blocking, never as a suggestion or unrealistic, because it was seen in real use. Its `- dość (planowanie): …` line may have no `file:line`.

## 1.11.1 — 2026-10-15

- `loc-planning` (`references/prd.md`) also replaces an old PRD header that still explains `→ przekazane` markers with the template's header, and tidies sections outside `Cel`, `Rdzeń idei` and `Kierunki`: a point the code shows is done moves into the `## Fragment PRD` of the plan that did it; a point with no such plan stays.

## 1.11.0 — 2026-10-15

- **The judge also decides at planning.** When `loc-planning` plans from a `utknelo`, `przeglad` or `odlozone` that lists review findings (`references/findings.md`, new), the `judge` agent weighs every Blocking and Non-blocking one first: `fix` goes into the plan, `enough` becomes a `- dość (planowanie): …` line in the new plan's `## Uwagi z przeglądów`, so its reviews do not raise it again. Suggestions and Unrealistic findings become lines there too and never go into a plan; speed comes back only when the user reports something noticeably slow. With no `fix` at all, no plan is written.
- `loc-planning` no longer asks the user which review findings to take, and no longer moves leftovers into `odlozone` files: in real use those files only fed the next plan of small cases, whose review got stuck again. An `odlozone` is only for a `fix` finding deliberately left out of a plan. Rule 3 says so.
- `check_state.py` accepts the gate `planowanie` in review notes.

## 1.10.0 — 2026-10-15

- **Judge.** A new `judge` agent weighs every Blocking and Non-blocking finding of a milestone code-review and of the final review: a broken criterion, `Invariants` entry or plan decision is fixed; otherwise it asks what the project's user loses if the finding stays (lost or distorted data, a crash, a wrong conclusion → fix; a small inaccuracy → `enough`); when unsure, fix. A review gate passes when the judge leaves nothing to fix. In real use every round of a review of free-form input found new cases (6, 7, then 9 findings, none breaking a criterion), and every plan ended in stuck gates that became the next plan.
- An `enough` verdict is a `- dość (<gate>): … Powód: …` line in the plan's `## Uwagi z przeglądów` (checked by `check_state.py`) and is not raised again. The final report of `loc-orchestrate` lists them, numbered and grouped by the PRD point they rest on; the user may answer "popraw 2".
- Rounds 2 and 3 of a milestone code-review review only the diff of the previous round's fixes. The final review still covers the whole plan.
- One `utknelo` file per plan run, one section per stuck gate (`references/stuck.md`, new; the `utknelo` template changed). Older files with one gate each are closed as before.
- **PRD holds only what is current.** The template has `## Cel`, `## Rdzeń idei` (the guidelines the judge reads, never handed to a plan) and `## Kierunki`. A `Kierunki` fragment that becomes a plan moves into the plan's `## Fragment PRD` section and leaves the PRD; old `→ przekazane` fragments are moved the same way at the next planning (`loc-planning` `references/prd.md`, new). `check_plan.py` treats `## Fragment PRD` as history.
- `loc-planning` proposes any change to `Cel` or `Rdzeń idei` (or both, when the PRD has none) in a `pytanie` titled `PRD:` and asks the user in the conversation; the PRD is written only after a yes. `loc-orchestrate` does not start while that `pytanie` is open. Rule 9 says the same.
- Rounds 2 and 3 keep the start of their fix diff in the gate's `review_from`, so a resumed run reviews the same fixes. `popraw N` after a report is an input for `loc-planning`.
- Existing projects need no manual change: the next `loc-planning` run proposes `Rdzeń idei` if it is missing and tidies the PRD.

## 1.9.0 — 2026-10-15

- A milestone's `Dowód` runs only the tests of its criteria plus the fast layers of `loc/TEST-PLAN.md` (a), never the full suite (`loc-planning` `references/tests.md`); `rubber-duck` reports a proof that runs the full suite as Blocking. The proof runs in every round of its gate, and in real use a ten-minute suite ran up to three times per milestone; `loc-qa` still runs the full suite once.
- The `TEST-PLAN.md` template asks for a fixed seed or deterministic mode in tests with random data (e.g. hypothesis), so a gate does not fail at random.

## 1.8.0 — 2026-09-30

- Every plan has a `## Nie bronimy przed` section: who produces inputs the code deliberately does not defend against, with the reason, or `- brak`. `loc-planning` proposes it and shows it in its report; `rubber-duck` checks it at the plan gate; `check_plan.py` rejects a plan without it or with an empty one. In real use, reviews of a security-related plan kept inventing a new attacker each round, and every gate ended stuck.
- A review finding whose input comes only from someone on that list is Unrealistic, quoting the list's line, and is not raised again (`gates.md`, `rubber-duck`).
- An open plan written before 1.8.0 fails `check_plan.py` in `loc-orchestrate` until the section is added; one line `- brak` is enough.

## 1.7.0 — 2026-09-30

- `loc-planning` adds a `Planowanie` entry to `loc/MEMORY.md` after the plan's gate, with one `memory_index.py` command (`references/closing.md`). New type `Planowanie` in `memory_index.py` and `loc-journal`.
- `memory_index.py` no longer loses entries from the index when an entry's text mentions `<!--`: only a line that starts with it opens a comment. In real use one such entry hid every older entry from the index; the next run of the script restores them. First tests of the script.

## 1.6.3 — 2026-09-30

- The write guard allows the directories listed in `permissions.additionalDirectories` of the project's own `.claude/settings.json` and `.claude/settings.local.json`; everything else outside the project is still denied. A project whose data directory lies outside it could not have its reports written by the model, and an `allow` rule does not lift a hook's denial.

## 1.6.1 — 2026-09-30

- A milestone's sub-agent is told to keep scratch files in `loc/tmp/` and delete only files it created there, never the directory; rule 2 says the same. The rules reach only the main session, and in real use a sub-agent told "delete it after" removed the whole `loc/tmp/` with files it had not created.
- Size budgets: rules 420 words, `loc-orchestrate` `SKILL.md` 920.

## 1.6.0 — 2026-09-29

- A fourth review category, Unrealistic (`nierealna`): a finding that needs an input nothing in the project produces. It must name who or what produces that input instead (`Kto to wytwarza:`); if it cannot, the finding is not unrealistic. A finding keeps its category from the milestone to the final review unless there is a new argument. In real use each review of a checker found another invented input, and each deferred file became the next plan.
- Suggestions and Unrealistic findings of review gates create no inbox file: one line each in the plan's `## Uwagi z przeglądów`, with the gate and no proposed fix. `check_state.py` checks the section's format and the `Kto to wytwarza:` answer. An inbox file is created only by a stuck gate, and the `utknelo` file shows its `**Kategoria:**` under `**Typ:**`. The state file's `deferred` field stays for runs started before 1.6.
- `loc-review` standalone lists the category first on each line and creates no file when every finding is Unrealistic. The `rubber-duck` agent reports Unrealistic findings as their own group.

## 1.5.0 — 2026-09-29

- At the end of a plan `loc-orchestrate` writes the diary entry itself with one `memory_index.py` command instead of starting `loc-journal`. It knows how the plan went, so the entry is the same; the skill's extra steps each re-read the whole end-of-plan context. The plan's end no longer tidies `loc/PATTERNS.md`: lessons go there when they are learned (rule 10). `loc-journal` stays for work outside orchestration.
- Scenario 09 checks the diary entry (E8).

## 1.4.0 — 2026-09-29

- Review gates have a severity threshold: a milestone's code-review and the final review fix Blocking and Non-blocking findings (code-review `high`, `medium`) and pass when none is left. Suggestions (`low`) are not fixed in the gate; they go to one `odlozone` file per plan, named in the state file's new optional `deferred` field (`check_state.py` checks it). In real use every gate fixed `low` findings round after round, went stuck after 3 rounds and widened the plan.
- After the last failed round of a gate no more code changes: a fix made then was never reviewed. The details of stuck gates moved to `loc-orchestrate/references/gates.md`.
- At the end of a plan, `loc-orchestrate` closes the follow-up files of its milestones (stuck `utknelo` files and the `deferred` file) whose every point the code now resolves: `## Rozstrzygnięcie` with the fix and `file:line`, then `loc/inbox/done/`. Partly resolved files stay open with the resolved points marked. Scenario `09-final-review-closes-resolved`.

## 1.3.0 — 2026-09-28

- Installation from a marketplace: the repository is its own marketplace (`.claude-plugin/marketplace.json`); `/plugin marketplace add etobod/masterskills`, then `/plugin install masterskills@masterskills`. README has an Installation section.
- The `M<n>/red` gate records `test_author`: for a milestone with a `(zachowanie)` criterion, `check_state.py` requires `true` (the `test-author` agent wrote those tests) or `false` with a deviation for that milestone.
- `Read` of a file, and `Glob` or `Grep` with a `path`, inside the plugin's own directory run without a prompt (`plugin_commands.py`, symlinks and `..` resolved first). An installed plugin lives outside the project, so every reference a skill opened asked for permission; the scenarios' settings had hidden this with an allow rule for the repository, now removed.
- `scripts/py.sh` runs Python with `-B`: hooks and scripts no longer leave `__pycache__/` inside the installed plugin.
- `loc-orchestrate` writes its state file with the Write or Edit tool; `loc-planning` reads the test-plan template at the plugin path instead of searching the disk for it.
- `loc-planning` leaves no files behind when it runs a command to verify it (`git status --short` unchanged; Python: `python -B`).
- The `qa` and `test-author` agents write test names, code and comments in English: the core rules reach only the main session, not agents.
- `check_plan.py` rejects this plugin's own expanded path in a plan (a plan must work on another machine); `loc-planning/references/tests.md` requires `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md`. Scenario 05 checks it.

## 1.2.0 — 2026-09-28

- Tests in planning: a code milestone lists acceptance criteria (`**Kryteria:**`, ``- K<n>: <what the code must do> → `<test>` ``, `(zachowanie)` for behaviour seen from outside) and a performer (`**Wykonawca:** auto | agent | użytkownik (blokujący|odkładalny)`); `check_plan.py` enforces both. The first plan with code starts with a test-suite milestone. Details in `loc-planning/references/tests.md`.
- Template `templates/loc/TEST-PLAN.md` (the project's test contract, created by the first plan with code, not by `loc-init`) and a `## Project-specific workflow` section in the `CLAUDE.md` template.
- Scenario `05-first-plan-with-code`.
- Tests in plan execution (`loc-orchestrate/references/tests.md`): tests before code with a red gate `M<n>/red` that must fail on an assertion (its output kept in the state file, validated by `check_state.py`); a test written after its code proves itself by one hand-made mutation.
- `scripts/test_baseline.py`: a copy of the project's tests at the start of a plan (`loc/state/<NNN>/baseline/`), `--compare` lists changed, added and removed tests.
- `scripts/mutate.py` (`backup` / `restore`); the `SessionStart` hook restores a file left mutated by an interrupted session.
- Agent `test-author`: writes the tests for behaviour criteria before the code, without reading the implementation.
- Scenario `06-test-before-code`.
- Skill `loc-qa` (forked, runs as the `qa` agent): runs the full suite once, compares the tests with the plan's copy, writes missing tests for criteria, runs the project's `qa-*` skills whose `qa-paths:` match the change, and writes `loc/state/<NNN>/qa.md` with APPROVED or NOT APPROVED. Changes tests only.
- Agent `qa`.
- `loc-orchestrate`: a `qa` phase and gate before the final review for plans with `**Kryteria:**`; a plan whose QA gets stuck stays open. `check_state.py` rejects `journal` or `done` for such a plan without a passed or stuck `qa` gate.
- Scenarios `07-qa-paths-field` and `08-qa-no-tests-temptation`.
- A criterion may name its test by the id the framework runs directly (`test_app.TestGreet.test_polish`) as well as by file and test name.
- `PostToolUse` hook `after_push.py`: after a successful `git push` in a project with GitHub Actions workflows, one CI check with `gh run list`; a failed run becomes a `utknelo` inbox file. `plugin_commands.py` allows exactly that `gh run list` command.
- A `utknelo` file quotes the failure output of every round, also when it repeats the previous one (template and `loc-orchestrate`).
- README: the `loc/` workflow, `loc/TEST-PLAN.md`, `loc-qa` and the `test-author` agent.

## 1.1.0 — 2026-09-28

- All workflow files of a project live in `loc/`, ignored by git with one `.gitignore` line: `loc/inbox/`, `loc/PRD.md`, `loc/PATTERNS.md`, `loc/MEMORY.md`, plan state in `loc/state/`, review diffs in `loc/review/`, scratch files in `loc/tmp/`. `loc-init` no longer adds `tmp/` to `.gitignore` or `.gitkeep` files.
- Plans are closed with `mv` only: nothing in `loc/` is tracked.
- Templates moved to `templates/loc/`.
- Repeatable tests for the hooks and the `loc-init`/inbox scripts in `tests/` (`python -m unittest discover -s tests`).

## 1.0.1 — 2026-09-28

- `rules/core.md` rule 3: every inbox file is created with `next_number.py`, never by hand; rule 11 shortened to stay within the word budget.
- `SessionStart` context lists the inbox commands (`next_number.py` with the plugin path, `mv inbox/<file> inbox/done/`), to be run alone in the Bash tool so they need no approval.
- Scenario `04-question-in-conversation`: a question in plain conversation creates no file; a chat answer to a `pytanie` is recorded, moved to `inbox/done/` and becomes an `odlozone` file.

## 1.0.0 — 2026-09-26

- `rules/core.md`: the always-loaded rules (12 points + 7a).
- `SessionStart` hook (startup, /clear, compaction): injects the rules and the project's open inbox; `scripts/py.sh` finds a working Python 3 on Windows and macOS.
- `scripts/inbox_summary.py`: open `inbox/` files and plan state files as JSON.
- `loc-init` skill and `scripts/init_project.py`: set up `inbox/`, `docs/` (PRD, PATTERNS, MEMORY), the `CLAUDE.md` sections and `tmp/` in `.gitignore`; idempotent, never overwrites, refuses a directory that is not a git root.
- `templates/`: the six inbox types, the three `docs/` files and the `CLAUDE.md` sections.
- `loc-brainstorm` skill: one growing brainstorm file in `inbox/` with numbered decisions (`B-01`…); records only.
- `loc-planning` skill: turns an inbox file, a PRD fragment or text into a plan with milestones and proofs, gated by `check_plan.py` and `rubber-duck` (at most 3 rounds, then `utknelo`); closes its input.
- `researcher` and `rubber-duck` agents (read-only).
- `scripts/next_number.py`: next inbox number, and creates an inbox file from its template with the time from the clock.
- `scripts/check_plan.py`: mechanical plan gate (sections, undecided phrases, placeholders, milestones = proofs).
- `loc-orchestrate` skill: executes a plan inline or with a sub-agent per milestone; a proof gate and a `code-review` gate per milestone (at most 3 rounds each, then `utknelo`), deviation rules 1–4, a closed list of stops, final `loc-review`, plan to `inbox/done/`, a proposed commit message and no commit.
- `loc-review` skill: `rubber-duck` and `code-review` in parallel with an explicit level (never `ultra`), project invariants and `❌` patterns; fixes the findings after a plan (at most 3 rounds), or reports to a `przeglad` file when run on its own.
- `scripts/check_state.py`: validates `tmp/state/<NNN>.json`, including the 3-round limit and its `utknelo` file.
- `scripts/snapshot.py`: a milestone snapshot as a dangling commit object (new files included), recorded in the state file; history, index and working tree stay untouched.
- `inbox_summary.py`: finished runs (`phase: done`) are no longer reported as active.
- `scripts/memory_index.py`: keeps `docs/MEMORY.md` newest first, regenerates its index, trims to N entries (default 1000); adds an entry stamped with the clock; idempotent.
- `loc-journal` skill: one short diary entry per piece of work (`Plan`, `Przegląd`, `Poprawka`, `Decyzja`), corrects contradicted `PATTERNS.md` entries; never touches `docs/PRD.md`.
- `loc-orchestrate` calls `loc-journal` after closing the plan (`phase: journal`).
- `PreToolUse` hook `write_guard.py`: writes only inside the project, no exceptions; best-effort check of `Bash` and `PowerShell` redirections, `tee` and write cmdlets.
- `PreToolUse` hook `commit_guard.py`: denies `git commit` with AI attribution markers; ordinary mentions of AI pass.
- `loc-init` adds `.claude/settings.json` (`autoMemoryEnabled: false`, empty `attribution`), filling in only missing values (nested objects and lists included).
- `PreToolUse` hook `plugin_commands.py`: allows the skills' own commands (the plugin's scripts, `date +…`, moves from `inbox/` to `inbox/done/`) without a prompt; skills run each command on its own.
- `scripts/review_diff.py`: `loc-review` writes its diff through a script instead of a shell redirection.
- Scenario headings in English (`Setup`, `Steps`, `Expected`); results recorded under `## Result`.

## 0.1.0 — 2026-09-26

- Plugin skeleton: manifest, standard directory layout.
- `scripts/measure.py`: enforces the word budget for rules, skills, references and agents.
- `scenarios/`: README and the first three behaviour scenarios.
