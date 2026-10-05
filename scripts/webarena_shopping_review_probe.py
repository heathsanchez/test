#!/usr/bin/env python3
import asyncio,json
from playwright.async_api import async_playwright
URL="http://localhost:7770/ostent-16gb-memory-card-stick-storage-for-sony-ps-vita-psv1000-2000-pch-z081-z161-z321-z641.html"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(headless=True); page=await b.new_page()
    r=await page.goto(URL,wait_until="networkidle",timeout=120000)
    sels=[".review-item","#reviews",".reviews-actions",".product-reviews-summary","a[href*='review']","[data-role='collapsible']",".items.review-items"]
    out={"status":r.status if r else None,"url":page.url,"title":await page.title(),"body":(await page.locator("body").inner_text())[:20000],"selectors":{}}
    for s in sels:
      loc=page.locator(s); vals=[]
      for i in range(min(20,await loc.count())):
        vals.append({"text":(await loc.nth(i).inner_text())[:2000],"html":(await loc.nth(i).inner_html())[:4000],"href":await loc.nth(i).get_attribute("href")})
      out["selectors"][s]=vals
    print(json.dumps(out,indent=2,ensure_ascii=False)); await b.close()
asyncio.run(main())
