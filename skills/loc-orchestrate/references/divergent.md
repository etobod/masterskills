# Divergent milestones

A **divergent milestone** (`**Kind:** divergent`) makes something the user has not fixed and that has no single right answer: a name, a tagline, a visual direction, a concept. Its risk is not a bug but the first answer everyone gives. It is built as variants that differ in kind, judged by a critic, and picked by the user.

## Planning: when, and its fields

Divergent when the result is a name, a text, a visual direction or a concept the user has not decided. Never for identifiers in code, bug fixes, or texts whose form a project rule sets (README, commit messages, changelog).

```
### M3 — app name and tagline
**Kind:** divergent
**Default:** a two-syllable made-up word with a gradient logo; "Your text, simplified"
**Facts:** PRD Goal: counts and cleans text for one person; CLAUDE.md: a terminal tool
**Working parts:** the name is typed in a terminal: lowercase, no spaces, `python -B check_name.py` exits 0
**Variants:** 3
**Proof:** `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --check --log loc/state/<NNN>/divergent-M3.md` → `ok`
```

- **Default**: the answer most people would give first, written out, so it can be avoided on purpose.
- **Facts**: two or three facts of this project (the PRD, `CLAUDE.md`, the code) the variants start from; `seed` when the project gives none, then `seed.py` gives the start.
- **Working parts**: what must keep working whatever the look or words (a form still submits, a name still types); a command where one can check it.
- **Variants**: 2 to 4, 3 by default. No `**Criteria:**`.

## Running it

The log is `loc/state/<NNN>/divergent-M<n>.md`; every step writes to it through `divergent_log.py`.

1. **Default.** `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --start --log <log> --default "<Default>"`.
2. **Start.** Read `**Facts:**` and `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/moves.py show --last 12`. With `seed`: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/seed.py visual|text|idea` (a look, a text, a concept) for each variant, `--keep <axis>=<value>` for an axis the project fixes. The seed is a start, never a rule: a variant may move away from it with a reason.
3. **Variants.** Make each one different in kind, not in degree: another means, not another shade. You write text and concepts; the `designer` agent sketches visual ones (sketches, never the full build). At most one is the **safe** variant, close to the default but better; mark it. Record each: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --variant --log <log> --name A --move "<the means, e.g. a name from the one verb the tool does>" --reason "<one sentence naming a fact>" [--safe]`. Keep the working parts whole in every variant.
4. **Critic.** The `design-critic` agent in `divergent` mode, given the milestone's `Default`, `Facts`, `Working parts`, the variants and `loc/moves.md`. Record each verdict: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --verdict --log <log> --name A --result pass|fail --why "<its sentence>"`. A failed variant is reworked once (`--variant` again with the same name, which clears its verdict, then the critic on it again) or dropped. At least 2 must pass; fewer after the rework: the milestone is stuck (`stuck.md`).
5. **Pick.** Recommend one: the strongest reason, not the safest. Add a `### M<n>: pick a variant` to the plan's one `question` file (as in `run.md`, rule 4), added to `questions`: each passed variant as an option with a preview (the text, or the sketch's screenshot), the recommended one first, and `None of them`. Then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --pick --log <log> --name <recommended> --by interim` and go on: the plan never waits for the pick.
6. **Build.** Build the picked variant in full (the `designer` for a look) and check the working parts (their command, if any), then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/moves.py add "<its move>" --plan <NNN>` and `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --built --log <log> --working pass|fail`; failing working parts are fixed first. The proof now prints `waiting: user pick`: the milestone is `done`, its pick waiting in `questions`, never stuck.

## The user's answer

`loc-orchestrate` asks the pick with the other questions and records it: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/divergent_log.py --pick --log <log> --name <variant>|none --by user`.

- **The recommended variant**: the proof prints `ok`.
- **Another variant**: a `deferred` file (core rule 8): build that variant, `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/moves.py remove "<the recommended move>"`, add its own move, `--built`.
- **None of them** (`--name none`): a `deferred` file asks for new variants once (`--start` again), the rejected ones added to its `**Default:**`; a second `None of them` becomes a `question` file asking the user what they want instead.

## Rules

- A variant's reason names a fact of this project; "it looks modern" is not a reason.
- Moves name the means, never the content: `a tagline written as a timetable`, not the tagline.
- The critic judges and never picks; the user picks; you only recommend.
- Cost: variants are sketches, roughly two to three times the milestone; only the picked one is built in full.
