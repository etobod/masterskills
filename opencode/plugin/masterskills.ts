// masterskills for OpenCode: runs the plugin's Python hooks, the same ones Claude Code runs.
// opencode/build.py copies this file to <config>/plugins/ and fills in the path below.
// Reading the plugin's files without a prompt is set in opencode.json by the install.
import { spawnSync } from "node:child_process"
import { readFileSync } from "node:fs"

const ROOT = "@@MASTERSKILLS_ROOT@@" // <config>/masterskills: scripts, hooks, rules
const PYTHONS = ["python3", "python", "py"]

// Which hook runs for which Claude Code tool: read from the plugin's own hooks.json,
// so OpenCode runs exactly what Claude Code runs. Event -> [matcher, hook name][].
function hookTable(): Record<string, [RegExp, string][]> {
  const table: Record<string, [RegExp, string][]> = {}
  try {
    const config = JSON.parse(readFileSync(`${ROOT}/hooks/hooks.json`, "utf-8")).hooks
    for (const event of Object.keys(config))
      for (const group of config[event])
        for (const h of group.hooks ?? []) {
          const name = /hooks\/(\w+)\.py/.exec(h.command ?? "")?.[1]
          if (name) (table[event] ??= []).push([new RegExp(`^(?:${group.matcher ?? ".*"})$`), name])
        }
  } catch {}
  return table
}
const HOOKS = hookTable()
const hooksFor = (event: string, tool: string) => (HOOKS[event] ?? []).filter(([m]) => m.test(tool)).map(([, n]) => n)

// OpenCode tool name -> Claude Code tool name and input.
function claudeCall(tool: string, args: any): { name: string; input: any }[] {
  switch (tool) {
    case "bash":
      return [{ name: "Bash", input: { command: args.command ?? "" } }]
    case "write":
      return [{ name: "Write", input: { file_path: args.filePath, content: args.content } }]
    case "edit":
      return [{ name: "Edit", input: { file_path: args.filePath } }]
    case "read":
      return [{ name: "Read", input: { file_path: args.filePath } }]
    case "glob":
      return [{ name: "Glob", input: { pattern: args.pattern, path: args.path } }]
    case "grep":
      return [{ name: "Grep", input: { pattern: args.pattern, path: args.path } }]
    case "patch":
    case "apply_patch": {
      const text = String(args.patchText ?? args.patch ?? "")
      return [...text.matchAll(/^\*\*\* (?:Add|Update|Delete) File: (.+)$/gm)].map((m) => ({
        name: "Write",
        input: { file_path: m[1].trim() },
      }))
    }
    default:
      return []
  }
}

let python: string | null | undefined
function findPython(): string | null {
  if (python !== undefined) return python
  python = null
  for (const candidate of PYTHONS) {
    const probe = spawnSync(candidate, ["-c", "import sys; sys.exit(sys.version_info[0] != 3)"])
    if (probe.status === 0) {
      python = candidate
      break
    }
  }
  return python
}

// Runs hooks/<name>.py with the hook input on stdin; its JSON output, or null.
function hook(name: string, data: object, directory: string): any {
  const py = findPython()
  if (!py) return null
  const run = spawnSync(py, ["-B", `${ROOT}/hooks/${name}.py`], {
    input: JSON.stringify(data),
    encoding: "utf-8",
    env: {
      ...process.env,
      CLAUDE_PLUGIN_ROOT: ROOT,
      CLAUDE_PROJECT_DIR: directory,
      MASTERSKILLS_PYTHON: py,
      PYTHONIOENCODING: "utf-8",
    },
    timeout: 10000,
  })
  try {
    return run.stdout ? JSON.parse(run.stdout) : null
  } catch {
    return null
  }
}

export const Masterskills = async ({ directory }: { directory: string }) => {
  const rules = new Map<string, string>()

  return {
    // The PreToolUse hooks (write guard, commit guard): a deny stops the tool with the hook's reason.
    "tool.execute.before": async (input: any, output: any) => {
      for (const call of claudeCall(input.tool, output.args ?? {})) {
        for (const name of hooksFor("PreToolUse", call.name)) {
          const data = { hook_event_name: "PreToolUse", tool_name: call.name, tool_input: call.input, cwd: directory }
          const decision = hook(name, data, directory)?.hookSpecificOutput
          if (decision?.permissionDecision === "deny") throw new Error(decision.permissionDecisionReason)
        }
      }
    },

    // The PostToolUse hooks (the state file check after a write, the CI check after `git push`):
    // their text is appended to the tool's output. Claude Code runs them only after a call that succeeded.
    "tool.execute.after": async (input: any, output: any) => {
      if (input.tool === "bash" && typeof output.metadata?.exit === "number" && output.metadata.exit !== 0) return
      for (const call of claudeCall(input.tool, input.args ?? {})) {
        for (const name of hooksFor("PostToolUse", call.name)) {
          const data = { hook_event_name: "PostToolUse", tool_name: call.name, tool_input: call.input, cwd: directory }
          const context = hook(name, data, directory)?.hookSpecificOutput?.additionalContext
          if (context) output.output = `${output.output ?? ""}\n\n${context}`
        }
      }
    },

    // The SessionStart hooks (core rules, open inbox): computed once per session and again after compaction.
    "experimental.chat.system.transform": async (input: any, output: any) => {
      const key = input.sessionID ?? ""
      if (!rules.has(key)) {
        const data = { hook_event_name: "SessionStart", source: "startup", cwd: directory }
        const texts = hooksFor("SessionStart", "startup").map((n) => hook(n, data, directory)?.hookSpecificOutput?.additionalContext)
        rules.set(key, texts.filter(Boolean).join("\n\n"))
      }
      // Appended to the last part, not pushed as a new one: OpenCode sends each part as its own
      // system message, and chat templates such as Qwen's accept only one, at the beginning.
      const text = rules.get(key)
      if (!text) return
      if (output.system.length) output.system[output.system.length - 1] += `\n\n${text}`
      else output.system.push(text)
    },

    event: async ({ event }: any) => {
      if (event?.type === "session.compacted") rules.delete(event.properties?.sessionID ?? "")
    },

    // The skills' commands find the plugin and the project as they do in Claude Code.
    "shell.env": async (_input: any, output: any) => {
      output.env.CLAUDE_PLUGIN_ROOT = ROOT
      output.env.CLAUDE_PROJECT_DIR = directory
    },
  }
}
