# masterskills — core rules

1. **Language.** English for everything in the project, `loc/` included. Only the text of a `question` file is in the `User language` of `CLAUDE.md`. Talk to the user in their language.
2. **Stay in the project.** Write only inside the project. Scratch files go to `loc/tmp/`, never `/tmp`, `%TEMP%` or the scratchpad. Delete only files you created there, never the directory. Directories in `permissions.additionalDirectories` count as the project.
3. **Inbox.** A file in `loc/inbox/` is open work; `U` after its number (`088-U-question-…`) marks the user's. Create inbox files with the `next_number.py` command under Inbox. A decision for the user, in a skill or not, goes first to the `architect` agent (Decide): within its competence apply its ruling; beyond it, a `question` file at once, and work continues on the recommended option unless that is expensive to undo. Deferred work becomes a `deferred` file. A quick clarification stays in chat.
4. **Code is the only source of truth.** Never document the current state of the code.
5. **Commits.** Never add `Co-authored-by`, session links or any mention of AI.
6. **Gates.** Every gate (plan check, rubber-duck, code-review, tests) gets at most 3 rounds, then record them where the skill says and carry on.
7. **Flow.** Planning talk goes into the active `brainstorm` file in `loc/inbox/` (`loc-brainstorm`). Plans are made only by `loc-planning` and executed only by `loc-orchestrate`.
7a. After work outside a plan that actually changed something, `loc-journal` adds an entry to `loc/MEMORY.md`.
8. **Answered questions.** When the user answers a `question` (in chat or in the file; "as the architect recommends" is an answer too), write the answer under `## Resolution` and move the file to `loc/inbox/done/`. An answer other than the interim option the work used gets a `deferred` file with what must change. Name an option by file, letter and content (`088 A: finish the entry`), never bare.
9. **PRD.** `loc/PRD.md` holds only what is current. `Goal`, `Core idea` and `Scenarios` change only with the user's consent (`loc-planning`). A `Directions` fragment moves into the plan made from it. A fragment marked `→ moved to …` is not authoritative. Precedence: code > plan in progress > `Directions`.
10. **Patterns.** Before running or configuring something, check `loc/PATTERNS.md`. When a command or setup fails and another way works (not a fixed typo), record it first: `✅` what works, `❌` what failed, each with **When to use**.
11. **User vocabulary.** "Turn off 1M token": `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` in `settings.json` `env`; "turn on": remove it, or `/model opus[1m]`. Both apply next session.
12. **Decisions are not dogma.** When you see a better solution than the user's, propose it with reasons.
13. **Tests with the user.** A short overview, then one step per message: `Step 1/N`, what to install or open, the exact text to type, "paste the reply". Check files yourself.
