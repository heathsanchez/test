#!/usr/bin/env python3
import asyncio, json
from playwright.async_api import async_playwright

BASE="http://localhost:7780/admin"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        r=await page.goto(BASE+"/customer/index/",wait_until="networkidle",timeout=120000)
        out={"status":r.status if r else None,"url":page.url,"title":await page.title(),"tables":[]}
        tables=page.locator("table")
        for i in range(await tables.count()):
            t=tables.nth(i)
            th=t.locator("thead th")
            headers=[]
            for j in range(await th.count()):
                headers.append((await th.nth(j).inner_text()).strip())
            out["tables"].append({
                "i":i,
                "visible":await t.is_visible(),
                "headers":headers,
                "rows":await t.locator("tbody tr").count(),
                "text":(await t.inner_text())[:5000],
            })
        out["body"]=(await page.locator("body").inner_text())[:20000]
        print(json.dumps(out,indent=2))
        await browser.close()

asyncio.run(main())
