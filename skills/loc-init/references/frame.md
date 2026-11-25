# The project frame: draft it, ask once

No goal, no work. Every plan and review is weighed against the **frame**: `loc/PRD.md` `## Goal`, `## Core idea` and `## Scenarios`, and a test command in `CLAUDE.md` `## Commands`. A skill that needs it runs:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/frame.py
```

`ok: true`: go on, read no further. Otherwise `missing` lists what is empty. Do this in the main session, before any agent starts: an agent cannot ask the user.

## 1. Draft

Draft every missing part at once, in English, from what already exists, in this order:

1. the user's words in this conversation and the description given to `loc-init`;
2. open and done brainstorms in `loc/inbox/` (`## Topic`, `## Decisions`, `## Notes`), plans and `loc/MEMORY.md`;
3. the code: `README`, the package manifest, the entry points.

- **Goal**: what the project is for and for whom, two to four sentences.
- **Core idea**: two to five points, each a priority with its reason (`**Data first.** …`), not a description of the code.
- **Scenarios**: three to seven numbered uses: who, what they do, what they expect to see.
- **Test command**: from the project files (`package.json` `scripts.test`, `pyproject.toml`, `Makefile`, an existing `tests/` folder). No tests at all: propose the language's built-in runner (`python -m unittest`, `node --test`); the first plan sets the suite up.

Never invent a fact the sources do not give. A part with no source at all is drafted as a question in the text (`Who uses it: <you tell me>`), not a guess.

## 2. Ask

Show the exact text of each part, then one `AskUserQuestion`, in the user's language:

- **Accept** (recommended): written exactly as shown.
- **Correct in my words**: the user writes what is wrong; redraft and ask again, the same three options.
- **Reject**: stop. Write nothing; tell the user the work cannot start without the frame and list `missing`.

This first fill of an empty part is the window question; core rule 9's `PRD:` `question` file is only for changing a part that is already filled.

## 3. Write

Replace each section's template comment or placeholder, keep the heading; a missing heading goes in from `${CLAUDE_PLUGIN_ROOT}/templates/loc/PRD.md`, before `## Directions`. The test command goes as a line in `CLAUDE.md` `## Commands` (`- Tests: \`<command>\``). Run `frame.py` again: it must print `ok: true`. Then go back to the step that asked for the frame.

## From a description (`loc-init` with free text)

The user described the project once; nothing they wrote may be lost.

1. The structure first: `init_project.py` as usual.
2. The frame from the description: sections 1 to 3 above, in one question. In the same question show what else the description gives for `CLAUDE.md` (`Commands`, `Frontend`, `Limits`, `User language`), filled only where those sections are empty.
3. The rest is work: a new brainstorm (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type brainstorm --slug "<topic>" --title "<topic>" --source "loc-init description" --by loc-init`). `## Topic`: one paragraph. `## Notes`: the description edited, every fact, name, link and number kept, nothing that went into the frame repeated. `## Open`: each unclear point, with a recommendation when there is one. No decisions: the user has not made any yet.
4. Report in one line that the user can keep talking in that brainstorm or plan it with `/masterskills:loc-planning <NNN>`.
