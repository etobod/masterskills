# Design: milestones that change what the user sees

With a user interface: the `designer` agent builds, `ui_check.py` measures, the `design-critic` agent judges, and the user rates it on the checks sheet.

## `## Frontend` in `CLAUDE.md`

```
## Frontend
UI check: sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/ui_check.py
Screenshots: on
References: on
Tokens: src/styles/tokens.css
Widths: 375, 768, 1440
Pages: index.html
Scene views: none
Design plugin: none
```

- **Screenshots**: `on`, or `declined <date>` when the user refused the browser.
- **References**: `on` (look at good pages on the same subject) or `off`.
- **Tokens**: the one file holding every colour, size and space; the first UI milestone creates it.
- **Pages**: what to open, a file or a local address (`http://localhost:5173/`) with its start command.
- **Scene views**: the project's own screenshot command for states an address cannot reach (a 3D scene, a state set through controls) and its output directory, or `none`.
- **Design plugin**: an external design plugin and its review command, or `none`. It is an addition; the plugin's own agents always run.

## Filled by `loc-init`

`loc-init` fills an empty `## Frontend` as soon as it sees a user interface, with the Edit tool (never a script: Windows paths break its string escapes):

- `UI check`, `References: on`, `Widths: 375, 768, 1440` and `Design plugin: none` as above;
- `Screenshots`: after `ui_check.py --detect` and the question under Tools;
- `Pages`: the entry page (`index.html`), or the dev server address with its start command from `Commands`;
- `Tokens: none yet`: the first UI milestone creates the file and writes its path here.

## Tools

`ui_check.py --detect` says whether Playwright is installed. When it is not and `Screenshots` is not `declined`, ask with `AskUserQuestion` once: `Install the browser` (recommended: the critic sees the page, the sheet gets screenshots; the command is in `install`) or `No screenshots`. Record a refusal as `Screenshots: declined <date>` and never ask again. Without screenshots the critic judges from code; sheet points have no images.

## References

With `References: on`, before the first UI milestone of a plan and when a brainstorm needs visual directions, the `researcher` agent finds 3–5 good pages on the subject. Its query uses general words about the subject ("bike repair shop booking page"), never the project's name, files or the user's text. Screenshot each one:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/ui_check.py --url <address> --widths 1440,375 --out loc/tmp/design/references --name ref-<k>
```

Then a note per reference, `loc/tmp/design/references/ref-<k>.md`: its address, the principles worth taking (the grid, the type pairing, the density) and what not to take. References give principles, never assets: no images, code, logos or text are copied. They stay for the next plans.

## A UI milestone

1. **Build**: the `designer` agent, with the milestone, the visual direction (its brainstorm or PRD decision), the tokens file, the reference notes and screenshots, the critic's earlier notes and the files it may change.
2. **Proof**: besides the tests, a `**Proof:**` line per check, each exiting 0 (with `Screenshots: declined`, only the second); a page from a dev server adds `--serve "<its start command>"`:

   ```sh
   sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/ui_check.py --url <page> --widths <Widths> --check
   sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/ui_check.py --tokens <Tokens> --files <changed UI files>
   ```

   A defect (horizontal scroll, cut-off text, contrast below WCAG AA, no visible focus, a raw colour or size outside the tokens) is fixed like a failing test.
3. **Screenshots**: `ui_check.py --url <page> --widths <Widths> --out loc/tmp/design/shots/<NNN> --name M<n>`, and the `Scene views` command when the milestone changes such a state; both go to the critic and sheet. None with `Screenshots: declined`.
4. **Light review** (gate `M<n>/design`): the `design-critic` agent in `light` mode, with the screenshots, the direction, the tokens and the changed files. A Blocking finding goes back to the `designer` with the notes, then steps 2–4 again; at most 3 rounds (core rule 6). Notes go to `## Review notes` as `- suggestion (M<n> design): …`.

## End of the plan

1. **Full review**: the final review (`loc-review`) runs the `design-critic` agent in `full` mode, with the last screenshots of every changed screen, the references and the light notes. Its findings to fix go to the `designer`; after each round the checks and screenshots run again, within the final review's 3 rounds.
2. **Checks sheet**: one point per changed screen, with its screenshots and a reference beside them:

   ```sh
   sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/checks.py --add --plan <NNN> --milestone <M> --title "Look of <screen>" --step "Open <page>" --look "<what the direction promised>" --image "loc/tmp/design/shots/<NNN>/M<n>-375.png | 375 px" --image "loc/tmp/design/shots/<NNN>/M<n>-1440.png | 1440 px" --reference "loc/tmp/design/references/ref-1-1440.png | reference"
   ```

   A `fix` rating is a new round: the `designer` with the user's words, the checks, new screenshots, a new point with `--again`.
3. Delete `loc/tmp/design/shots/<NNN>/`: the sheet keeps its own copies.

## A design plugin

When `Design plugin` names one, its review command runs too, read-only, beside the full review; its findings join the critic's with the tag `[design]`.
