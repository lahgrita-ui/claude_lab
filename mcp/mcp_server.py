import json
from pathlib import Path

import obsidiantools.api as otools
from fastmcp import FastMCP

try:
    import pyomd  # py-obsidianmd; requires setuptools on Python ≥ 3.12
    _PYOMD_AVAILABLE = True
except ImportError:
    _PYOMD_AVAILABLE = False

OBSIDIAN_CONFIG = Path.home() / "Library/Application Support/obsidian/obsidian.json"

mcp = FastMCP("obsidian-mcp", instructions="MCP server for reading and editing Obsidian vaults.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_vaults() -> dict:
    if not OBSIDIAN_CONFIG.exists():
        return {}
    return json.loads(OBSIDIAN_CONFIG.read_text()).get("vaults", {})


def _vault_path(vault_path: str) -> Path:
    p = Path(vault_path)
    if not p.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")
    return p


def _open_vault(vault_path: str) -> otools.Vault:
    return otools.Vault(_vault_path(vault_path)).connect().gather()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_vaults() -> list[dict]:
    """List all Obsidian vaults registered in the Obsidian desktop app."""
    vaults = _load_vaults()
    return [
        {"id": vid, "path": meta.get("path"), "open": meta.get("open", False)}
        for vid, meta in vaults.items()
    ]


@mcp.tool()
def edit_vault(vault_path: str, action: str, target: str, new_name: str = "") -> str:
    """Manage vault structure.

    Actions:
    - create_folder: creates a subdirectory at target path inside the vault.
    - create_note: creates an empty markdown note at target (e.g. "folder/note.md").
    - rename_note: renames the note at target to new_name (filename only, keep extension).
    - delete_note: deletes the note at target.
    """
    root = _vault_path(vault_path)
    node = root / target

    if action == "create_folder":
        node.mkdir(parents=True, exist_ok=True)
        return f"Folder created: {node}"

    if action == "create_note":
        node.parent.mkdir(parents=True, exist_ok=True)
        if node.suffix != ".md":
            node = node.with_suffix(".md")
        node.touch()
        return f"Note created: {node}"

    if action == "rename_note":
        if not node.exists():
            raise FileNotFoundError(f"Note not found: {node}")
        dest = node.parent / (new_name if new_name.endswith(".md") else new_name + ".md")
        node.rename(dest)
        return f"Renamed {node.name} → {dest.name}"

    if action == "delete_note":
        if not node.exists():
            raise FileNotFoundError(f"Note not found: {node}")
        node.unlink()
        return f"Deleted: {node}"

    raise ValueError(f"Unknown action: {action}. Use create_folder, create_note, rename_note, or delete_note.")


@mcp.tool()
def read_document(vault_path: str, note_name: str) -> str:
    """Read the markdown source of a note by its filename stem (no .md extension).

    Example: note_name="Meeting Notes" reads Meeting Notes.md from the vault.
    """
    vault = _open_vault(vault_path)
    if note_name not in vault.md_file_index:
        available = list(vault.md_file_index.keys())[:20]
        raise ValueError(f'Note "{note_name}" not found. Available (first 20): {available}')
    return vault.get_source_text(note_name)


@mcp.tool()
def edit_document(vault_path: str, note_name: str, content: str) -> str:
    """Overwrite a note with new markdown content. Creates the note if it does not exist.

    note_name is the filename stem (no .md) or a relative path inside the vault.
    """
    root = _vault_path(vault_path)

    # Try to locate existing note via obsidiantools first
    try:
        vault = _open_vault(vault_path)
        if note_name in vault.md_file_index:
            note_path = vault.md_file_index[note_name]
        else:
            note_path = root / (note_name + ".md")
    except Exception:
        note_path = root / (note_name + ".md")

    note_path = Path(note_path)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(content, encoding="utf-8")
    return f"Saved {note_path.relative_to(root)}"


# ---------------------------------------------------------------------------
# Resources  (official documentation excerpts)
# ---------------------------------------------------------------------------

@mcp.resource(
    "obsidian://docs/obsidian",
    name="obsidian-docs",
    description="Obsidian concepts: vaults, notes, links, frontmatter, and folder structure.",
    mime_type="text/markdown",
)
def docs_obsidian() -> str:
    return """\
# Obsidian — Key Concepts

## Vault
A vault is a folder on your file system. Every markdown file inside it is a **note**.
Obsidian stores app settings in `<vault>/.obsidian/`.

## Notes
Notes are plain `.md` files. They support YAML frontmatter (between `---` delimiters)
for metadata such as tags, aliases, and dates.

## Links
- **Wikilinks**: `[[Note Name]]` or `[[Note Name|alias]]`
- **Markdown links**: `[alias](Note%20Name.md)`
- **Embeds**: `![[Note Name]]`

## Tags
Inline `#tag` or frontmatter `tags: [tag1, tag2]`.

## Canvas
`.canvas` files store visual boards with JSON; they live alongside `.md` files.

## Folder Structure Best Practices
- Keep flat or use shallow nesting (≤ 3 levels).
- Use frontmatter `type:` to classify notes instead of deep folders.
- Templates live in a dedicated folder referenced in Settings › Templates.

Official docs: https://help.obsidian.md
"""


@mcp.resource(
    "obsidian://docs/obsidiantools",
    name="obsidiantools-docs",
    description="obsidiantools Python API: Vault, connect, gather, and analysis methods.",
    mime_type="text/markdown",
)
def docs_obsidiantools() -> str:
    return """\
# obsidiantools

PyPI: `obsidiantools`  — analyse an Obsidian vault from Python.

## Quick start
```python
import obsidiantools.api as otools
from pathlib import Path

vault = otools.Vault(Path("/path/to/vault")).connect().gather()
```

## Key methods
| Method | Returns | Notes |
|---|---|---|
| `connect()` | Vault | Builds wikilink graph |
| `gather()` | Vault | Loads source text of every note |
| `get_source_text(name)` | str | Raw markdown; requires gather() |
| `get_readable_text(name)` | str | Plain text (HTML stripped) |
| `get_note_metadata()` | DataFrame | One row per note |
| `get_wikilinks(name)` | list | Outgoing wikilinks |
| `get_backlinks(name)` | list | Incoming wikilinks |
| `get_tags(name)` | list | Inline + frontmatter tags |
| `get_front_matter(name)` | dict | Parsed YAML frontmatter |
| `md_file_index` | dict[str,Path] | name → absolute Path |

## Notes
- `file_name` is the **stem** (no `.md`), not the full path.
- Call `connect()` before graph methods; `gather()` before text methods.

GitHub: https://github.com/mfarragher/obsidiantools
"""


@mcp.resource(
    "obsidian://docs/fastmcp",
    name="fastmcp-docs",
    description="FastMCP Python SDK: tools, resources, prompts, and client usage.",
    mime_type="text/markdown",
)
def docs_fastmcp() -> str:
    return """\
# FastMCP

PyPI: `fastmcp` — high-level Python SDK for the Model Context Protocol.

## Server
```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(x: int) -> str:
    return str(x)

@mcp.resource("data://info")
def my_resource() -> str:
    return "some info"

@mcp.prompt()
def my_prompt(topic: str) -> str:
    return f"Write about {topic}"

if __name__ == "__main__":
    mcp.run()
```

## Client (async)
```python
from fastmcp import Client

async with Client("server.py") as client:
    tools    = await client.list_tools()
    result   = await client.call_tool("my_tool", {"x": 42})
    prompts  = await client.list_prompts()
    prompt   = await client.get_prompt("my_prompt", {"topic": "AI"})
    resources = await client.list_resources()
    content  = await client.read_resource("data://info")
```

Docs: https://gofastmcp.com
"""


@mcp.resource(
    "obsidian://docs/py-obsidianmd",
    name="py-obsidianmd-docs",
    description="py-obsidianmd (pyomd) Python API for reading and patching Obsidian notes.",
    mime_type="text/markdown",
)
def docs_py_obsidianmd() -> str:
    available = "AVAILABLE" if _PYOMD_AVAILABLE else "NOT AVAILABLE (requires setuptools; broken on Python ≥ 3.12)"
    return f"""\
# py-obsidianmd (pyomd)

PyPI: `py-obsidianmd`  —  Status in this environment: {available}

## Purpose
Read and write Obsidian note metadata (frontmatter) and content programmatically.

## Key Classes
```python
from pyomd import Notes
from pyomd.metadata import MetadataType

notes = Notes("/path/to/vault")
note  = notes.get(path="folder/note.md")

# Read frontmatter
note.metadata.get(meta_type=MetadataType.FRONTMATTER, key="tags")

# Update frontmatter
note.metadata.update(meta_type=MetadataType.FRONTMATTER, key="status", value="done")
note.write()
```

GitHub: https://github.com/Lkruitwagen/py-obsidianmd
"""


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt()
def patch_document(
    vault_path: str,
    note_name: str,
    search_text: str,
    replacement_text: str,
) -> str:
    """Prompt for editing a vault note via targeted MD patch (find-and-replace section)
    instead of a full rewrite. Reduces risk of losing unchanged content.
    """
    return f"""\
You are editing an Obsidian note using a targeted patch — do NOT rewrite the whole file.

Vault : {vault_path}
Note  : {note_name}

Steps:
1. Call read_document(vault_path="{vault_path}", note_name="{note_name}") to get the current content.
2. Locate the exact section matching:
   ---SEARCH---
   {search_text}
   ---END SEARCH---
3. Replace only that section with:
   ---REPLACEMENT---
   {replacement_text}
   ---END REPLACEMENT---
4. Call edit_document(vault_path="{vault_path}", note_name="{note_name}", content=<patched_content>)
   with the full file content after the substitution.
5. Confirm the number of characters changed.

Rules:
- Preserve all frontmatter (YAML between --- delimiters) unless the patch targets it.
- Preserve all wikilinks [[...]] and tags #tag outside the patched section.
- If search_text appears more than once, patch only the first occurrence and warn the user.
"""


@mcp.prompt()
def vault_summary(vault_path: str) -> str:
    """Prompt that asks the model to produce a ≤ 250-character summary of vault content."""
    return f"""\
Analyse the Obsidian vault at: {vault_path}

Using list_vaults and read_document, scan the notes in the vault.

Return a single plain-text summary of the vault's main topics and purpose.

Hard constraints:
- Maximum 250 characters (count them).
- No markdown, no bullet points — one flowing sentence or two short ones.
- Include the vault name, dominant themes, and approximate note count if available.

Example format:
"Sunny vault (42 notes): personal knowledge base covering AI research, book summaries, and weekly reviews. Main areas: ML papers, productivity, and project planning."
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
