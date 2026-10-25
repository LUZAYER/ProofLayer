"""Capture verified UI states of the new ProofLayer Homepage, Evaluation, and Operations Cockpit."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACTS_DIR = Path("/home/luzayer/.gemini/antigravity-ide/brain/1d5b862b-bd51-49d8-b69a-e74971d7ddaf")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Navigating to http://localhost:3000...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await asyncio.sleep(2)

        # 1. Capture clean English Homepage
        print("Capturing English Homepage...")
        await page.screenshot(path=str(ARTIFACTS_DIR / "homepage_en.png"))

        # 2. Click language toggle to switch to Bengali
        print("Toggling language to Bengali...")
        lang_btn = page.locator("#lang-toggle-btn")
        if await lang_btn.count() > 0:
            await lang_btn.click()
        else:
            await page.get_by_text("বাংলা").first.click()
        await asyncio.sleep(1)

        # Capture Bengali Homepage
        print("Capturing Bengali Homepage...")
        await page.screenshot(path=str(ARTIFACTS_DIR / "homepage_bn.png"))

        # 3. Switch back to English
        print("Switching back to English...")
        if await lang_btn.count() > 0:
            await lang_btn.click()
        else:
            await page.get_by_text("EN").first.click()
        await asyncio.sleep(1)

        # 4. Click nav "Overview"
        print("Navigating to Overview Console...")
        overview_nav = page.locator("nav button").nth(1)
        await overview_nav.click()
        await asyncio.sleep(2)
        await page.screenshot(path=str(ARTIFACTS_DIR / "console_overview.png"))

        # 5. Click nav "Evaluation & Benchmarks"
        print("Navigating to Evaluation & Benchmarks...")
        eval_nav = page.locator("nav button").nth(2)
        await eval_nav.click()
        await asyncio.sleep(2)
        await page.screenshot(path=str(ARTIFACTS_DIR / "console_evaluation.png"))

        # 6. Click nav "Approvals Queue"
        print("Navigating to Approvals Queue...")
        approvals_nav = page.locator("nav button").nth(5)
        await approvals_nav.click()
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(ARTIFACTS_DIR / "console_approvals.png"))

        # 7. Click nav "Proof & Audit Ledger"
        print("Navigating to Proof & Audit Ledger...")
        audit_nav = page.locator("nav button").nth(8)
        await audit_nav.click()
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(ARTIFACTS_DIR / "console_audit.png"))

        # 8. Click nav "Policies"
        print("Navigating to Policies...")
        policies_nav = page.locator("nav button").nth(6)
        await policies_nav.click()
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(ARTIFACTS_DIR / "console_policies.png"))

        print("All visual captures complete!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
