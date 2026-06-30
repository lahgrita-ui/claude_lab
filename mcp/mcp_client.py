"""Async client for the Obsidian MCP server."""

import asyncio
from pathlib import Path

from fastmcp import Client

SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

async def list_tools() -> list[dict]:
    """Return all tools exposed by the server."""
    async with Client(SERVER_SCRIPT) as client:
        tools = await client.list_tools()
        return [
            {"name": t.name, "description": t.description}
            for t in tools
        ]


async def call_tool(tool_name: str, arguments: dict) -> str:
    """Call a named tool with the given arguments and return the text result."""
    async with Client(SERVER_SCRIPT) as client:
        result = await client.call_tool(tool_name, arguments)
        # result is CallToolResult; text lives in result.content list
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

async def list_prompts() -> list[dict]:
    """Return all prompts exposed by the server."""
    async with Client(SERVER_SCRIPT) as client:
        prompts = await client.list_prompts()
        return [
            {"name": p.name, "description": p.description}
            for p in prompts
        ]


async def get_prompt(prompt_name: str, arguments: dict) -> str:
    """Render a prompt by name with given arguments and return the message text."""
    async with Client(SERVER_SCRIPT) as client:
        result = await client.get_prompt(prompt_name, arguments)
        # result is GetPromptResult; messages is list[PromptMessage]
        parts = []
        for msg in result.messages:
            content = msg.content
            if hasattr(content, "text"):
                parts.append(content.text)
            else:
                parts.append(str(content))
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

async def list_resources() -> list[dict]:
    """Return all static resources exposed by the server."""
    async with Client(SERVER_SCRIPT) as client:
        resources = await client.list_resources()
        return [
            {"uri": str(r.uri), "name": r.name, "description": r.description}
            for r in resources
        ]


async def read_resource(uri: str) -> str:
    """Fetch the content of a resource by URI."""
    async with Client(SERVER_SCRIPT) as client:
        result = await client.read_resource(uri)
        parts = []
        for item in result:
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

async def _demo():
    print("=== Tools ===")
    for t in await list_tools():
        print(f"  {t['name']}: {t['description']}")

    print("\n=== Prompts ===")
    for p in await list_prompts():
        print(f"  {p['name']}: {p['description']}")

    print("\n=== Resources ===")
    for r in await list_resources():
        print(f"  {r['uri']} — {r['name']}")

    print("\n=== list_vaults tool ===")
    print(await call_tool("list_vaults", {}))

    print("\n=== vault_summary prompt ===")
    vaults = await call_tool("list_vaults", {})
    import json as _json
    vault_list = _json.loads(vaults)
    if vault_list:
        first_vault = vault_list[0]["path"]
        print(await get_prompt("vault_summary", {"vault_path": first_vault}))

    print("\n=== obsidian://docs/obsidian resource ===")
    print(await read_resource("obsidian://docs/obsidian"))


if __name__ == "__main__":
    asyncio.run(_demo())
