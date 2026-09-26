# masterskills

A universal, project-independent workflow for Claude Code, shipped as a plugin: brainstorm, plan, orchestrate, review and journal, with always-loaded rules, hooks and helper scripts. Everything project-specific lives in the target project's `CLAUDE.md`.

## Requirements

- **git.** The project root must be a git repository: plans snapshot every milestone with git, reviews read the diff and work ends in a commit. `loc-init` refuses a directory without git.
- **Python 3** on `PATH` as `python3`, `python` or `py`. Hooks and skills run the plugin's helper scripts with it.
- **A POSIX `sh`.** Hooks and skills start scripts through `sh scripts/py.sh`. macOS and Linux have it. **On Windows install Git for Windows (Git Bash)**; without it the `SessionStart` hook and the skills' scripts fail.

## Getting started

In a project, run `/masterskills:loc-init`. It creates `inbox/`, `docs/` (PRD, PATTERNS, MEMORY), the standard `CLAUDE.md` sections, a `tmp/` entry in `.gitignore` and `.claude/settings.json` (Claude's auto memory off, since lessons go to `docs/PATTERNS.md`; no AI attribution in commits and pull requests). It only adds what is missing, so run it again after updating the plugin.

## Guards

Three `PreToolUse` hooks apply wherever the plugin is enabled:

- **The skills' own commands run without a prompt.** A `Bash` command that is exactly one of the plugin's scripts (`sh "<plugin>/scripts/py.sh" scripts/<name>.py …`), `date +<format>`, or a move of one file from `inbox/` to `inbox/done/` is allowed. Anything with `;`, `&&`, a pipe, a redirection or a `$` goes through the normal permission rules, so skills run each command on its own.
- **Writes stay in the project.** `Write`, `Edit` and `NotebookEdit` outside the project directory are denied, with no exceptions (this includes Claude's auto memory and plan-mode plan files: lessons go to `docs/PATTERNS.md`, plans through `loc-planning`, scratch files to `tmp/`). For `Bash` and `PowerShell` only redirections, `tee` and the common PowerShell write cmdlets are checked; `cp`, `mv`, scripts and paths behind unknown variables are not.
- **No AI attribution in commits.** A `git commit` carrying `Co-authored-by` Claude/Anthropic, "Generated with Claude Code", a `claude.ai/code` link or `noreply@anthropic.com` is denied. Mentioning AI in the message itself is fine.

A deny from a guard wins over the allow. Skills declare no `allowed-tools`: when the model starts a skill itself, those rules can reach the permission check after the skill's first command, and a skill with them needs approval before it starts. These are plugin hooks: a managed setting that allows only managed hooks (`allowManagedHooksOnly`) turns all of them off.

See `CHANGELOG.md` for changes between versions.
