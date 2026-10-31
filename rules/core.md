# masterskills — core rules

1. **Language.** English for everything in the project, `loc/` included. A `question` file's text is in the `User language` of `CLAUDE.md`. Talk to the user in their language.
2. **Stay in the project.** Write only inside the project. Scratch files go to `loc/tmp/`, never `/tmp`, `%TEMP%` or the scratchpad. Delete only files you created there. `permissions.additionalDirectories` count as the project.
3. **Inbox.** A file in `loc/inbox/` is open work; `U` after its number (`088-U-question-…`) marks the user's. Create them with `next_number.py` (Inbox). A decision for the user, in a skill or not, goes first to the `architect` agent (Decide): within its competence apply its ruling; beyond it, a `question` file at once, and work continues on the recommended option unless that is expensive to undo. Deferred work becomes a `deferred` file. A quick clarification stays in chat; a question the user may miss never does.
4. **Code is the only source of truth.** Never document the current state of the code.
5. **Commits.** Never add `Co-authored-by`, session links or any mention of AI.
6. **Gates.** Every gate (plan check, rubber-duck, code-review, tests) gets at most 3 rounds, then record them and carry on.
7. **Flow.** Planning talk goes into the active `brainstorm` file (`loc-brainstorm`). Plans are made only by `loc-planning` and executed only by `loc-orchestrate`.
7a. After work outside a plan that changed something, `loc-journal` adds an entry to `loc/MEMORY.md`.
8. **Answered questions.** When the user answers a `question` (in chat or in the file; "as the architect recommends" is an answer too), write the answer under `## Resolution` and move the file to `loc/inbox/done/`. When work waits on one, also ask it with `AskUserQuestion`: the file, its options, recommended first. An answer other than the interim option gets a `deferred` file with what must change. Name an option by file, letter and content (`088 A: finish the entry`), never bare.
9. **PRD.** `loc/PRD.md` holds only what is current. `Goal`, `Core idea` and `Scenarios` change only with the user's consent in a `PRD:` `question` file, also outside a plan. A `Directions` fragment moves into the plan made from it. A fragment marked `→ moved to …` is not authoritative. Precedence: code > plan in progress > `Directions`.
10. **Patterns.** Before running or configuring something, check `loc/PATTERNS.md`. When a command fails and another way works, record it first: `✅` what works, `❌` what failed, each with **When to use**.
11. **User vocabulary.** "Turn off 1M token": `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` in `settings.json` `env`; "turn on": remove it, or `/model opus[1m]`. Both apply next session.
12. **Decisions are not dogma.** Propose a better solution than the user's, with reasons.
13. **Tests with the user.** A short overview, then one step per message: `Step 1/N`, what to install or open, the exact text to type, "paste the reply". Check files yourself.
