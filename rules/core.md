# masterskills — core rules

1. **Language.** English for everything in the project, `loc/` included. Only the text of a `question` file is in the `User language` of `CLAUDE.md`. Talk to the user in their language.
2. **Stay in the project.** Write files only inside the project directory. Scratch files go to `loc/tmp/`, never `/tmp`, `%TEMP%` or the session scratchpad. Delete only files you created there, never the directory. Directories in the project's `permissions.additionalDirectories` count as the project.
3. **Inbox.** A file in `loc/inbox/` means something waits for the user. Create every inbox file with the `next_number.py` command shown under Inbox, never by hand. Inside a skill, a question or deferred work becomes a file in `loc/inbox/` in the same reply (`NNN-question-…`, `NNN-deferred-…`), and work continues on the recommended option. Stop only when that choice would be expensive to undo. A review finding the judge did not mark `fix` is not deferred work. In plain conversation the user tracks their own questions.
4. **Code is the only source of truth.** Never document the current state of the code.
5. **Commits.** Never add `Co-authored-by`, session links or any mention of AI.
6. **Gates.** Every gate (plan check, rubber-duck, code-review, tests) gets at most 3 rounds. Then write `loc/inbox/NNN-stuck-…` with the full record and carry on.
7. **Flow.** When a conversation turns into planning, notes go into the active `brainstorm` file in `loc/inbox/` (`loc-brainstorm`). Plans are made only by `loc-planning` and executed only by `loc-orchestrate`.
7a. After work outside a plan that actually changed something, `loc-journal` adds an entry to `loc/MEMORY.md`.
8. **Answered questions.** When the user answers a `question` (in chat or in the file), write the answer under `## Resolution` and move the file to `loc/inbox/done/`. If the answer differs from the interim option the work already used, create a `deferred` file with what must change.
9. **PRD.** `loc/PRD.md` holds only what is current. `Goal`, `Core idea` and `Scenarios` are the project's guidelines, changed only with the user's consent (`loc-planning`). A `Directions` fragment moves into the plan made from it. An old fragment marked `→ moved to …` is not authoritative. Precedence: code > plan in progress > `Directions`.
10. **Patterns.** Before running or configuring something, check `loc/PATTERNS.md`. When a command or setup fails and another way works (another path, shell, tool or flag, not a fixed typo), record it before the next step: `✅` the way that works, `❌` the one that failed, each with **When to use**.
11. **User vocabulary.** "Turn off 1M token": set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` in `settings.json` `env`. "Turn on": remove it, or `/model opus[1m]`. Both apply next session; say so.
12. **Decisions are not dogma.** When you see a better solution than the user's decision, propose it with reasons.
