#!/usr/bin/env python3
import asyncio, json
from playwright.async_api import async_playwright

BASE="http://localhost:9999"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"})
        page=await ctx.new_page()
        for path in ["/f/worcester","/f/worcester/new","/f/Worcester","/f/Worcester/new"]:
            try:
                r=await page.goto(BASE+path,wait_until="networkidle",timeout=60000)
                body=(await page.locator("body").inner_text())[:16000]
                links=await page.locator("a").evaluate_all("(els)=>els.slice(0,120).map(a=>({text:(a.innerText||'').trim(),href:a.href,class:a.className}))")
                print(json.dumps({"path":path,"status":r.status if r else None,"url":page.url,"title":await page.title(),"body":body,"links":links},indent=2))
            except Exception as e:
                print(json.dumps({"path":path,"error":str(e)}))
        await browser.close()
asyncio.run(main())
