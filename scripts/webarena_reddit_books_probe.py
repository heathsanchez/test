#!/usr/bin/env python3
import asyncio, json
from playwright.async_api import async_playwright

BASE="http://localhost:9999"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context()
        page=await ctx.new_page()
        r=await page.goto(BASE+"/f/books/hot",wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200:
            raise RuntimeError("books hot page failed")
        posts=page.locator("article, .submission")
        out=[]
        for i in range(min(10,await posts.count())):
            post=posts.nth(i)
            link=post.locator("a.submission__link").first
            if await link.count()==0:
                continue
            title=(await link.inner_text()).strip()
            href=await link.get_attribute("href")
            out.append({"rank":i+1,"title":title,"href":href})
        for row in out:
            detail=await ctx.new_page()
            href=row["href"]
            if href and href.startswith("/"):
                href=BASE+href
            resp=await detail.goto(href,wait_until="networkidle",timeout=120000)
            row["status"]=resp.status if resp else None
            row["url"]=detail.url
            body=detail.locator("body")
            row["body"]=(await body.inner_text())[:20000]
            await detail.close()
        print(json.dumps(out,indent=2,ensure_ascii=False))
        await browser.close()

asyncio.run(main())
