#!/usr/bin/env python3
import asyncio,json
from playwright.async_api import async_playwright
BASE="http://localhost:7770"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(headless=True)
    ctx=await b.new_context(extra_http_headers={"X-M2-Customer-Auto-Login":"emma.lopez@gmail.com:Password.123"})
    page=await ctx.new_page()
    r=await page.goto(BASE+"/sales/order/history/",wait_until="networkidle",timeout=180000)
    out={"status":r.status if r else None,"url":page.url,"title":await page.title(),"body":(await page.locator("body").inner_text())[:30000],"links":[]}
    links=page.locator("a")
    for i in range(await links.count()):
      a=links.nth(i); href=await a.get_attribute("href"); txt=(await a.inner_text()).strip()
      if href and ("order" in href.lower() or "view" in txt.lower()):
        out["links"].append({"text":txt,"href":href})
    print(json.dumps(out,indent=2,ensure_ascii=False))
    await b.close()
asyncio.run(main())
