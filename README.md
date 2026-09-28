# masterskills

A universal, project-independent workflow for Claude Code, shipped as a plugin: brainstorm, plan, orchestrate, review and journal, with always-loaded rules, hooks and helper scripts. Everything project-specific lives in the target project's `CLAUDE.md`.

## Requirements

- **git.** The project root must be a git repository: plans snapshot every milestone with git, reviews read the diff and work ends in a commit. `loc-init` refuses a directory without git.
- **Python 3** on `PATH` as `python3`, `python` or `py`. Hooks and skills run the plugin's helper scripts with it.
- **A POSIX `sh`.** Hooks and skills start scripts through `sh scripts/py.sh`. macOS and Linux have it. **On Windows install Git for Windows (Git Bash)**; without it the `SessionStart` hook and the skills' scripts fail.

## Installation

The repository is its own marketplace (`.claude-plugin/marketplace.json`). In Claude Code:

```
/plugin marketplace add etobod/masterskills
/plugin install masterskills@masterskills
```

The repository is private: adding the marketplace clones it with git, so git on that machine needs access to `etobod/masterskills`. From a local clone, add the marketplace by its path instead (`/plugin marketplace add <path to the clone>`). Restart Claude Code after installing.

To update: `/plugin marketplace update masterskills`, then `/plugin update masterskills@masterskills`, restart, and run `/masterskills:loc-init` in each project.

## Getting started

In a project, run `/masterskills:loc-init`. It creates `loc/` (inbox, `PRD.md`, `PATTERNS.md`, `MEMORY.md`), the standard `CLAUDE.md` sections, a `loc/` entry in `.gitignore` and `.claude/settings.json` (Claude's auto memory off, since lessons go to `loc/PATTERNS.md`; no AI attribution in commits and pull requests). It only adds what is missing, so run it again after updating the plugin.

## Workflow

Every workflow file lives in `loc/`, ignored by git with one line: the inbox (`loc/inbox/`, done items in `loc/inbox/done/`), `PRD.md`, `PATTERNS.md`, `MEMORY.md`, plan state (`loc/state/`), review diffs (`loc/review/`) and scratch files (`loc/tmp/`).

- `loc-brainstorm` turns a conversation into decisions; `loc-planning` turns them into a plan whose code milestones list acceptance criteria, each with its test, and a performer.
- `loc/TEST-PLAN.md` is the project's test contract: layers and their commands, what to extend when the product changes, and how a test looks here. The first plan with code creates it.
- `loc-orchestrate` executes a plan milestone by milestone: tests first with a red gate that must fail on an assertion (the `test-author` agent writes behaviour tests without reading the code), then the code, the proof and a code review. It keeps a copy of the tests from the start of the plan.
- `loc-qa` gives the QA verdict, APPROVED or NOT APPROVED: the full suite once, the tests compared with that copy, a test for every criterion, and the project's own `qa-*` skills whose `qa-paths:` header matches the change. It changes tests only. `loc-orchestrate` runs it before the final review; run `/masterskills:loc-qa` yourself at any time.
- `loc-review` reviews the diff; `loc-journal` records lessons.

## Guards

Three `PreToolUse` hooks and one `PostToolUse` hook apply wherever the plugin is enabled:

- **The skills' own commands run without a prompt.** A `Bash` command that is exactly one of the plugin's scripts (`sh "<plugin>/scripts/py.sh" scripts/<name>.py …`), `date +<format>`, a move of one file from `loc/inbox/` to `loc/inbox/done/`, or the CI check `gh run list --branch <branch> --limit 1 --json status,conclusion,url` is allowed, and so are `Read` of a file and `Glob` or `Grep` inside the plugin's own directory (the skills' references and templates, wherever the plugin is installed). Anything with `;`, `&&`, a pipe, a redirection or a `$` goes through the normal permission rules, so skills run each command on its own.
- **Writes stay in the project.** `Write`, `Edit` and `NotebookEdit` outside the project directory are denied, with no exceptions (this includes Claude's auto memory and plan-mode plan files: lessons go to `loc/PATTERNS.md`, plans through `loc-planning`, scratch files to `loc/tmp/`). For `Bash` and `PowerShell` only redirections, `tee` and the common PowerShell write cmdlets are checked; `cp`, `mv`, scripts and paths behind unknown variables are not.
- **One CI check after a push.** After a successful `git push` in a project with `.github/workflows/`, the model checks the latest GitHub Actions run once. A failed run becomes a `utknelo` inbox file; a run in progress is mentioned, not waited for.
- **No AI attribution in commits.** A `git commit` carrying `Co-authored-by` Claude/Anthropic, "Generated with Claude Code", a `claude.ai/code` link or `noreply@anthropic.com` is denied. Mentioning AI in the message itself is fine.

A deny from a guard wins over the allow. Skills declare no `allowed-tools`: when the model starts a skill itself, those rules can reach the permission check after the skill's first command, and a skill with them needs approval before it starts. These are plugin hooks: a managed setting that allows only managed hooks (`allowManagedHooksOnly`) turns all of them off.

See `CHANGELOG.md` for changes between versions.
