"""Build the OpenCode version of masterskills from this repository.

The Claude Code plugin is the source; this script only translates it:

- `skills/<name>/` (SKILL.md and references): front matter cut to `name` and
  `description`;
- `commands/<name>.md`: a `/<name>` command per skill that loads it (OpenCode
  lists skills only in `/skills`, not as commands of their own); a skill with
  `context: fork` runs in its `agent` as a subtask;
- `agents/<name>.md`: `mode: subagent`, and `tools:` turned into `permission:`;
- `plugins/masterskills.ts`: runs the Python hooks from OpenCode's plugin hooks
  (write and commit guards, core rules and inbox in the system prompt, the CI
  check after a push);
- `masterskills/`: scripts, hooks, rules and templates, with `VERSION` and
  `MANIFEST` (every file this build wrote, so the next one removes only those).

A script command, `sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/<name>.py`,
becomes `<python> -B "<absolute path>"`: OpenCode on Windows runs commands in
PowerShell, which has no `sh`. `<python>` is the first of python3, python, py
that runs Python 3 at build time, as `py.sh` would choose.

`${CLAUDE_PLUGIN_ROOT}` in Markdown becomes an absolute path, since OpenCode has
no such variable, and the `masterskills:` prefix of skill and agent names goes.

Usage:
  python opencode/build.py --out <dir>   build into <dir>
  python opencode/build.py --install     build into the OpenCode config directory
                                         ($XDG_CONFIG_HOME/opencode, default
                                         ~/.config/opencode) and add to its
                                         opencode.json what projects need
Exit code 0 on success, 1 on an error.
"""

import argparse
import functools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = ("scripts", "hooks", "rules", "templates")
SKIPPED = re.compile(r"(__pycache__|\.pyc$)")
TEXT = {".md", ".json"}
RULES = "masterskills/rules/core.md"
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SCRIPT = re.compile(r'sh "\$\{CLAUDE_PLUGIN_ROOT\}/scripts/py\.sh" (\S+\.py)')
PYTHONS = ("python3", "python", "py")


@functools.lru_cache(maxsize=None)
def find_python() -> str:
    for candidate in PYTHONS:
        if not shutil.which(candidate):
            continue
        probe = subprocess.run([candidate, "-c", "import sys; sys.exit(sys.version_info[0] != 3)"],
                               capture_output=True)
        if probe.returncode == 0:
            return candidate
    return "python"


def front_matter(text: str) -> tuple:
    """Split `---` front matter into ({key: value}, body). Values are one line each."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("no front matter")
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields, text[match.end():]


def translate(text: str, out: Path) -> str:
    base = out.resolve().as_posix()
    text = SCRIPT.sub(lambda m: f'{find_python()} -B "{base}/masterskills/{m.group(1)}"', text)
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/skills/", f"{base}/skills/")
    text = text.replace("${CLAUDE_PLUGIN_ROOT}", f"{base}/masterskills")
    # Only Claude Code has a session id to resume; OpenCode's launcher needs none.
    text = text.replace(' --session "${CLAUDE_SESSION_ID}"', "")
    return re.sub(r"\bmasterskills:(?=[a-z])", "", text)


def skill(source: Path, out: Path) -> str:
    fields, body = front_matter(source.read_text(encoding="utf-8"))
    name, description = fields.get("name", ""), fields.get("description", "")
    if name != source.parent.name or not NAME.match(name):
        raise ValueError(f"{source}: name {name!r} must match the directory and {NAME.pattern}")
    if not 1 <= len(description) <= 1024:
        raise ValueError(f"{source}: description must have 1-1024 characters")
    head = f"---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n"
    return head + translate(body, out)


def command(source: Path) -> str:
    fields, _ = front_matter(source.read_text(encoding="utf-8"))
    head = f"---\ndescription: {json.dumps(fields['description'], ensure_ascii=False)}\n"
    if fields.get("context") == "fork" and fields.get("agent"):
        head += f"agent: {fields['agent'].removeprefix('masterskills:')}\nsubtask: true\n"
    return head + f"---\nLoad the `{fields['name']}` skill with the skill tool and follow it.\n\n$ARGUMENTS\n"


def agent(source: Path, out: Path) -> str:
    fields, body = front_matter(source.read_text(encoding="utf-8"))
    tools = {tool.strip() for tool in fields.get("tools", "").split(",")}
    edit = "allow" if tools & {"Write", "Edit"} else "deny"
    bash = "allow" if "Bash" in tools else "deny"
    head = (f"---\ndescription: {json.dumps(fields.get('description', ''), ensure_ascii=False)}\n"
            f"mode: subagent\npermission:\n  edit: {edit}\n  bash: {bash}\n---\n")
    return head + translate(body, out)


def files(out: Path) -> dict:
    """{relative output path: content (str) or source Path}."""
    result = {}
    for source in sorted((ROOT / "skills").glob("*/**/*.md")):
        rel = source.relative_to(ROOT).as_posix()
        result[rel] = skill(source, out) if source.name == "SKILL.md" else translate(
            source.read_text(encoding="utf-8"), out)
        if source.name == "SKILL.md":
            result[f"commands/{source.parent.name}.md"] = command(source)
    for source in sorted((ROOT / "agents").glob("*.md")):
        result[f"agents/{source.name}"] = agent(source, out)
    for top in PAYLOAD:
        for source in sorted((ROOT / top).rglob("*")):
            rel = source.relative_to(ROOT).as_posix()
            if source.is_dir() or SKIPPED.search(rel):
                continue
            target = f"masterskills/{rel}"
            result[target] = translate(source.read_text(encoding="utf-8"), out) \
                if source.suffix in TEXT else source
    base = out.resolve().as_posix()
    hooks = (ROOT / "opencode" / "plugin" / "masterskills.ts").read_text(encoding="utf-8")
    result["plugins/masterskills.ts"] = hooks.replace("@@MASTERSKILLS_ROOT@@", f"{base}/masterskills")
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    result["masterskills/VERSION"] = plugin["version"] + "\n"
    # init_project.py points open-code.bat at this repository's installer.
    result["masterskills/SOURCE"] = str(ROOT.resolve()) + "\n"
    return result


def build(out: Path) -> str:
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "masterskills" / "MANIFEST"
    new = files(out)
    old = manifest.read_text(encoding="utf-8").split() if manifest.exists() else []
    for rel in old:
        if rel not in new and (out / rel).is_file():
            (out / rel).unlink()
            parent = (out / rel).parent
            while parent != out and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    for rel, content in new.items():
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, Path):
            shutil.copyfile(content, target)
        else:
            target.write_text(content, encoding="utf-8", newline="\n")
    manifest.write_text("\n".join(sorted(new)) + "\n", encoding="utf-8", newline="\n")
    return new["masterskills/VERSION"].strip()


def configure(out: Path) -> list:
    """Add to opencode.json what every project needs, leaving the user's values alone:
    the project's CLAUDE.md in `instructions` (OpenCode skips it when an AGENTS.md
    exists) and reading the plugin's own files without a prompt. Also removes the
    core rules entry 1.13.0 added: the plugin now puts them in the system prompt.
    Returns what could not be added, for the user to add by hand."""
    config = out / "opencode.json"
    base = out.resolve().as_posix()
    allow = {f"{base}/masterskills/**": "allow", f"{base}/skills/**": "allow"}
    manual = ['"instructions": ["CLAUDE.md"]',
              '"permission": {"external_directory": ' + json.dumps(allow) + "}"]
    data = {"$schema": "https://opencode.ai/config.json"}
    if config.exists():
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except ValueError:
            return manual
        if not isinstance(data, dict):
            return manual
    missing = []
    instructions = data.setdefault("instructions", [])
    rules = (out / RULES).resolve().as_posix()
    if rules in instructions:
        instructions.remove(rules)
    if "CLAUDE.md" not in instructions:
        instructions.append("CLAUDE.md")
    permission = data.setdefault("permission", {})
    external = permission.setdefault("external_directory", {}) if isinstance(permission, dict) else None
    if isinstance(external, dict):
        for pattern, action in allow.items():
            external.setdefault(pattern, action)
    else:
        missing.append(manual[1])
    config.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path, help="build into this directory")
    target.add_argument("--install", action="store_true", help="build into the OpenCode config directory")
    args = parser.parse_args()
    if args.install:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        out = Path(base) / "opencode"
    else:
        out = args.out
    try:
        version = build(out)
    except (OSError, ValueError, KeyError) as error:
        print(f"masterskills: {error}", file=sys.stderr)
        return 1
    print(f"masterskills {version} -> {out.resolve().as_posix()}")
    if args.install:
        missing = configure(out)
        if missing:
            print(f"Could not edit {(out / 'opencode.json').as_posix()}; add by hand:")
            for line in missing:
                print(f"  {line}")
        print("Restart OpenCode to load it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
