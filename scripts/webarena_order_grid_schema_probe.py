#!/usr/bin/env python3
import asyncio, json, re
from playwright.async_api import async_playwright

BASE="http://localhost:7780/admin/sales/order/"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        await page.goto(BASE, wait_until="networkidle", timeout=120000)
        tables=page.locator("table")
        out={"url":page.url,"title":await page.title(),"tables":[]}
        for ti in range(await tables.count()):
            table=tables.nth(ti)
            th=table.locator("thead th")
            headers=[re.sub(r"\s+"," ",(await th.nth(i).inner_text()).strip()) for i in range(await th.count())]
            rows=[]
            tr=table.locator("tbody tr")
            for ri in range(min(await tr.count(),8)):
                td=tr.nth(ri).locator("td")
                cells=[]
                for ci in range(await td.count()):
                    cells.append(re.sub(r"\s+"," ",(await td.nth(ci).inner_text()).strip()))
                rows.append(cells)
            out["tables"].append({"index":ti,"headers":headers,"rows":rows})
        pagers=page.locator(".admin__data-grid-pager-wrap:visible")
        out["pagers"]=[]
        for i in range(await pagers.count()):
            w=pagers.nth(i)
            out["pagers"].append({
                "text":re.sub(r"\s+"," ",(await w.inner_text()).strip()),
                "next_disabled":await w.locator("button.action-next").is_disabled() if await w.locator("button.action-next").count() else None,
                "current":await w.locator('input[data-ui-id="current-page-input"]').input_value() if await w.locator('input[data-ui-id="current-page-input"]').count() else None,
            })
        print(json.dumps(out,indent=2))
        await browser.close()
asyncio.run(main())
