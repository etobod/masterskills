# masterskills

A universal, project-independent workflow for Claude Code, shipped as a plugin: brainstorm, plan, orchestrate, review and journal, with always-loaded rules, hooks and helper scripts. Everything project-specific lives in the target project's `CLAUDE.md`.

## Requirements

- **git.** The project root must be a git repository: plans snapshot every milestone with git, reviews read the diff and work ends in a commit. `loc-init` refuses a directory without git.
- **Python 3** on `PATH` as `python3`, `python` or `py`. Hooks and skills run the plugin's helper scripts with it.
- **A POSIX `sh`.** Hooks and skills start scripts through `sh scripts/py.sh`. macOS and Linux have it. **On Windows install Git for Windows (Git Bash)**; without it the `SessionStart` hook and the skills' scripts fail.

## Getting started

In a project, run `/masterskills:loc-init`. It creates `inbox/`, `docs/` (PRD, PATTERNS, MEMORY), the standard `CLAUDE.md` sections and a `tmp/` entry in `.gitignore`. It only adds what is missing, so run it again after updating the plugin.

See `CHANGELOG.md` for changes between versions.
