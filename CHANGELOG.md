# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

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
