# Claude Lab
This is a claude lab to show how to use some features Anthropic gives us to code better and faster.
claude code is a coding agent highly customizable and specialized on coding tasks
This labs explores one of its features at project and local level, doesnt cover managed org level configurations
## Instalation
```
brew install --cask claude-code
claude
/init
```
Install and open claude code, run init command to create or enhance CLAUDE.md file

## CLAUDE.md file
CLAUDE.md file is a markdown file with consise and effective rules loaded on every session to provide context.
- Use /init command on claude code to explore project and create CLAUDE.md file or improve existing one
- Use CLAUDE.local.md added to .gitignore file to use local rules
- Set Library/Application Support/ClaudeCode/CLAUDE.md for rules at organization level (or directly in managed-settings.json)
- Maintain CLAUDE.md file below 200 lines
- Use @ to import files with relative/absolute paths and `@` to mention docs literally without importing
- organize supporting files on .claude/rules/ and add frontmatter paths to restrict scope

### Automemory
This options allow Claude to store on ~/.claude/projects/<project>/memory/ knowledge notes for sessions

### / commands
inside .claude/commands/ put custom commands and invoke them like this /project:command-name custom commands are md files with a frontmatter indicating wich tools are allowed to use.

### hooks on project level settings.json
Hooks run shell commands automatically at specific points in Claude Code's lifecycle. They live in `.claude/settings.json` (committed, team-wide) or `.claude/settings.local.json` (local only).

Structure:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "ToolName",
        "hooks": [
          {
            "type": "command",
            "command": "your-shell-command"
          }
        ]
      }
    ]
  }
}
```

To block a tool call, the command outputs JSON with `hookSpecificOutput.permissionDecision: "deny"`.

### Use case

**CLAUDE.md rules + scoped rules**

We have a CLAUDE.md file, rules and a CLAUDE.local.md file, we have tested the prompt:
```
create a python hello world class with a hello world method in both @python_without_comment/ and @python_with_comment/
```
Claude code agent follows orders in CLAUDE.md as well as splited rules with path specific options, also adresses the local instruction for more customization in the suffix of objects literally that local file asked for 'use _var _func _Cls as sufix before each name for any variable, function or class definition'

**Custom command: enterprise watermarking**

Called custom slash command to add an enterprise watermark to a file:
```
/enterprise_code_watermarking @/Users/erick_c/Documents/Anthropic/Sunny_practice/python_without_comment/hello_world.py
```
This appended `# Pechan enterprises all rigths reserved 2026` at the end of the Python file using the `edit` tool (the only tool allowed in the command's frontmatter).

**Hook: block reading .env files**

Added a `PreToolUse` hook on the `Read` tool in `.claude/settings.json` to deny any read of a `.env` file:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path // \"\"' | { read -r f; echo \"$f\" | grep -qE '\\.env$' && echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"Reading .env files is blocked for security.\"}}'; }"
          }
        ]
      }
    ]
  }
}
```
Tested by asking Claude to read `.env` — the hook intercepted and returned the error before the file was accessed.

# skills

### commit_msg skill

Skills live in `.claude/skills/<name>/SKILL.md` and are invoked automatically when their trigger condition is met or when called explicitly. They extend Claude's default behavior within a session.

**Setup:** Created `.claude/skills/commit_msg/SKILL.md` with frontmatter declaring `name: commit_msg` and a body that instructs Claude to:
- Estimate the code review time based on number of files changed and lines changed
- Compute a 0–100 difficulty score: `(minutes − 1) × 10`, capped at 100 (< 1 min = 0, > 10 min = 100)
- Insert the score right after `type:` in the commit message, e.g. `feat[40]: ...`

**Skill file location:**
```
.claude/skills/commit_msg/SKILL.md
```

**How to invoke:** Ask Claude to commit changes and reference the skill:
```
commit everything, make sure to use commit msg skill
```

**Test result:** Committed 7 files (~156 lines changed). Estimated review time: 5 minutes → score = (5−1)×10 = **40**. Resulting commit message:
```
feat[40]: add Claude Code lab configuration, documentation, and commit_msg skill
```

# MCP — Obsidian MCP Server

Located in `mcp/`. A full Model Context Protocol server that lets any MCP client (Claude Desktop, custom clients, the MCP Inspector) read and edit Obsidian vaults.

**Stack:** FastMCP 3.4.2 · obsidiantools · py-obsidianmd · uv

### What was built

| File | Purpose |
|---|---|
| `mcp/mcp_server.py` | FastMCP server — tools, resources, prompts |
| `mcp/mcp_client.py` | Async Python client with list/call helpers |
| `mcp/main.py` | HTTP entry point with transport flag |

**Tools (4):** `list_vaults` · `edit_vault` (create/rename/delete notes & folders) · `read_document` · `edit_document`

**Resources (4):** `obsidian://docs/obsidian` · `obsidian://docs/obsidiantools` · `obsidian://docs/fastmcp` · `obsidian://docs/py-obsidianmd`

**Prompts (2):** `patch_document` (MD section patching, no full rewrite) · `vault_summary` (≤ 250-char vault digest)

### How to run

```bash
cd mcp

# Install
uv venv && uv add fastmcp obsidiantools py-obsidianmd

# HTTP server — MCP endpoint at http://127.0.0.1:8085/mcp
uv run main.py

# MCP Inspector (browser UI)
fastmcp dev inspector mcp_server.py

# Python client demo
uv run python mcp_client.py
```

See `mcp/README.md` for full setup, testing instructions, and Claude Desktop integration.
