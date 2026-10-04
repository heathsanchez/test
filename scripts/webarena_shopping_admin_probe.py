#!/usr/bin/env python3
import asyncio, urllib.parse
from playwright.async_api import async_playwright

BASE="http://127.0.0.1:7780"
PARAMS={
  "report_type":"created_at_order",
  "from":"01/01/2023",
  "to":"05/31/2023",
  "period":"month",
  "show_order_statuses":"1",
  "order_statuses[]":"complete",
}

async def main():
  async with async_playwright() as p:
    browser=await p.chromium.launch(headless=True)
    ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
    page=await ctx.new_page()
    url=BASE+"/admin/reports/report_sales/sales/filter?"+urllib.parse.urlencode(PARAMS,doseq=True)
    resp=await page.goto(url, wait_until="networkidle", timeout=120000)
    print("STATUS", resp.status if resp else None)
    print("URL", page.url)
    print("TITLE", await page.title())
    body=(await page.locator("body").inner_text())[:20000]
    print("BODY_START")
    print(body)
    print("BODY_END")
    print("TABLE_COUNT", await page.locator("table").count())
    for i in range(await page.locator("table").count()):
      txt=(await page.locator("table").nth(i).inner_text())[:12000]
      print(f"TABLE_{i}_START")
      print(txt)
      print(f"TABLE_{i}_END")
    await browser.close()
asyncio.run(main())
