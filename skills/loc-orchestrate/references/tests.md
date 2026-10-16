# Tests while executing a plan

For a milestone with `**Criteria:**`. Each criterion names its test; the goal is a test that really checks something, not one fitted to the code.

## At the start of the plan

Before the first milestone, copy the tests (once per plan; a resumed plan keeps its copy):

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/test_baseline.py --plan <NNN>
```

No `loc/TEST-PLAN.md` yet: nothing to copy, carry on (the first plan with code creates it).

## Test first, red on an assertion

Per milestone, in this order:

1. **Write the tests** the criteria name, in the files they name, following `loc/TEST-PLAN.md` section (e).
   - A criterion marked `(behaviour)`: the `test-author` agent writes its test **before** any code, from the criteria, TEST-PLAN (e) and the test file path only. Do not give it the implementation or your idea of it.
   - Other criteria: write the tests yourself.
   - *subagent* mode: start `test-author` yourself before the milestone's sub-agent (a sub-agent cannot start agents), and give that sub-agent this file's path.
2. **Stub.** Add the smallest code that lets the tests run and returns a wrong result (e.g. `return ""`), so an import or a missing name cannot be the failure.
3. **Red gate** (`M<n>/red`). Increase `rounds`, run the new tests. Every new test must fail **on its assertion** (`AssertionError`, `expected … got …`). An import, syntax or name error does not count: fix it and start the next round. A new test that passes on the stub checks nothing: fix the test. Passed: set `passed: true`, put the failing lines (assertion and test names, a few lines) in the gate's `output`, and with a `(behaviour)` criterion set `test_author` (`references/state.md`). After the third failed round: **stuck**, as for other gates.
4. **Real code**, then the proof gate.

## Test written after the code

A test added after its code (a regression test for a bug found on the way, a criterion the plan missed) proves itself by **mutation**, one hand-made change in place:

1. The test passes.
2. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/mutate.py backup <file>`
3. Break the code the test covers: flip a condition, change a returned value.
4. Run the test (Python: `python -B …`, so no bytecode of the mutated file is cached). It must fail on its assertion. Record it as an `M<n>/red` round with the output.
5. `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/mutate.py restore` — it checks the hash of the original.
6. The test passes again.

One mutation at a time; `backup` refuses a second one. Never restore with `git checkout`: the file may hold uncommitted work. An interrupted mutation is restored by the next session's start. Tests written before the code are not mutated.

## After each milestone

The milestone's proof, plus the fast layers from `loc/TEST-PLAN.md` section (a). The full suite runs once, in `loc-qa`.

## Weakening a test

Removing an assertion, loosening a condition, skipping a test or deleting one is allowed only openly: a deviation in the state file with the reason, repeated in the final report. Before the final review run `test_baseline.py --plan <NNN> --compare`; every existing test it lists as `changed` or `removed` needs such a deviation.

## Known defect

A test for a defect that stays open uses the strict marker from TEST-PLAN (e) (e.g. `xfail(strict=True)`) with the path of a `deferred` file in its reason; create that file with `next_number.py --type deferred`. When the test starts passing, the suite goes red: remove the marker, close the `deferred`.

## Fixtures

Fixtures committed to git are written by hand. Data recorded from real runs goes only to the ignored directory named in TEST-PLAN (e).
