# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

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
