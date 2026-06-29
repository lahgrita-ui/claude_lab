# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a learning lab for ebrew install --cask claude-code
claudexploring Claude Code features. The repo is used to experiment with CLAUDE.md rules, automemory, hooks, and other Anthropic tooling.

## Repo Structure

- `CLAUDE.md` — project-level rules (this file, committed)
- `.claude/CLAUDE.local.md` — local-only overrides (gitignored), adds `_var _func _Cls` suffix convention to all Python names
- `.claude/rules/naming_convention.md` — scoped rule for `python_without_suffix/`: suppresses all docstrings in that directory
- `.claude/commands/enterprise_code_watermarking.md` — custom `/project:enterprise_code_watermarking` command that appends a patent notice comment to a given file

## Python Rules

- Use descriptive names for variables, classes, and functions
- Add docstrings on each class or function following PEP conventions
- **Exception:** files under `python_without_suffix/` — no docstrings (enforced by @.claude/rules/naming_convention.md`)
