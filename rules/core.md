# masterskills — core rules

1. **Language.** English for everything in the project: code, comments, commits, skills, rules, `CLAUDE.md`, scripts. Polish only for the contents of `loc/`.
2. **Stay in the project.** Write files only inside the project directory. Scratch and temporary files go to `loc/tmp/`, never to `/tmp`, `%TEMP%` or the session scratchpad. Delete only files you created there, never the directory. Directories in the project's `permissions.additionalDirectories` count as the project.
3. **Inbox.** A file in `loc/inbox/` means something waits for the user. Create every inbox file with the `next_number.py` command shown under Inbox, never by hand. Inside a skill, a question or deferred work becomes a file in `loc/inbox/` in the same reply (`NNN-pytanie-…`, `NNN-odlozone-…`), and work continues on the recommended option. Stop only when that choice would be expensive to undo. In plain conversation the user tracks their own questions.
4. **Code is the only source of truth.** Never document the current state of the code.
5. **Commits.** Never add `Co-authored-by`, session links or any mention of AI.
6. **Gates.** Every gate (plan check, rubber-duck, code-review, tests) gets at most 3 rounds. Then write `loc/inbox/NNN-utknelo-…` with the full record and carry on.
7. **Flow.** When a conversation turns into planning, notes go into the active `brainstorm` file in `loc/inbox/` (`loc-brainstorm`). Plans are made only by `loc-planning`; plans are executed only by `loc-orchestrate`.
7a. After work outside a plan that actually changed something, `loc-journal` adds an entry to `loc/MEMORY.md`.
8. **Answered questions.** When the user answers a `pytanie` (in chat or in the file), write the answer under `## Rozstrzygnięcie` and move the file to `loc/inbox/done/`. If the answer differs from the interim option the work already used, create an `odlozone` file with what must change.
9. **PRD.** `loc/PRD.md` holds only what is current. `Cel` and `Rdzeń idei` are the project's guidelines, changed only with the user's consent (`loc-planning`). A `Kierunki` fragment moves into the plan made from it. An old fragment marked `→ przekazane do …` is not authoritative. Precedence: code > plan in progress > `Kierunki`.
10. **Patterns.** Before running or configuring something, check `loc/PATTERNS.md`. When you find a way that works, record it there at once.
11. **User vocabulary.** "Turn off 1M token" ("wyłącz 1M token"): set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` in `settings.json` `env`. "Turn on" ("włącz"): remove it, or `/model opus[1m]`. Both apply next session; say so.
12. **Decisions are not dogma.** When you see a better solution than the user's decision, propose it with reasons.
