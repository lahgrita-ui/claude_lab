"""Take screenshots of the MCP Inspector and save to mcp/assets/."""

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

TOKEN = os.environ.get("MCP_TOKEN", "")
BASE_URL = f"http://localhost:5078/?MCP_PROXY_PORT=3000&MCP_PROXY_AUTH_TOKEN={TOKEN}"
ASSETS = Path(__file__).parent / "assets"
ASSETS.mkdir(exist_ok=True)


async def screenshot(page, name: str, description: str):
    path = ASSETS / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    print(f"  saved {path.name}  ({description})")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        print("Opening inspector...")
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await screenshot(page, "01_inspector_home", "landing page before connect")

        # Click Connect
        print("Connecting...")
        connect_btn = page.get_by_role("button", name="Connect")
        await connect_btn.click()
        await page.wait_for_timeout(3000)
        await screenshot(page, "02_inspector_connected", "connected — server info visible")

        # Tools tab
        print("Tools tab...")
        await page.get_by_role("button", name="Tools").click()
        await page.wait_for_timeout(1000)
        await screenshot(page, "03_tools_list", "tools list (list_vaults, edit_vault, read_document, edit_document)")

        # Click list_vaults and run it
        print("Calling list_vaults...")
        await page.get_by_text("list_vaults").first.click()
        await page.wait_for_timeout(800)
        await screenshot(page, "04_tool_list_vaults", "list_vaults tool selected")

        run_btn = page.get_by_role("button", name="Run Tool")
        if await run_btn.count():
            await run_btn.click()
            await page.wait_for_timeout(2000)
            await screenshot(page, "05_tool_list_vaults_result", "list_vaults result — vaults JSON")

        # Resources tab
        print("Resources tab...")
        await page.get_by_role("button", name="Resources").click()
        await page.wait_for_timeout(1000)
        await screenshot(page, "06_resources_list", "resources list — 4 obsidian://docs/* URIs")

        # Read one resource
        obsidian_res = page.get_by_text("obsidian-docs").first
        if await obsidian_res.count():
            await obsidian_res.click()
            await page.wait_for_timeout(1500)
            await screenshot(page, "07_resource_obsidian_docs", "obsidian://docs/obsidian content")

        # Prompts tab
        print("Prompts tab...")
        await page.get_by_role("button", name="Prompts").click()
        await page.wait_for_timeout(1000)
        await screenshot(page, "08_prompts_list", "prompts list — patch_document, vault_summary")

        # vault_summary prompt
        vault_summary = page.get_by_text("vault_summary").first
        if await vault_summary.count():
            await vault_summary.click()
            await page.wait_for_timeout(800)
            await screenshot(page, "09_prompt_vault_summary", "vault_summary prompt with argument field")

        await browser.close()
        print(f"\nDone — {len(list(ASSETS.glob('*.png')))} screenshots in mcp/assets/")


if __name__ == "__main__":
    asyncio.run(main())
