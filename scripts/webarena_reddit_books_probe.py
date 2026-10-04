#!/usr/bin/env python3
import asyncio, json
from playwright.async_api import async_playwright

BASE="http://localhost:9999"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"})
        page=await ctx.new_page()
        r=await page.goto(BASE+"/f/books/hot",wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200:
            raise RuntimeError("books hot page failed")
        posts=page.locator(".submission")
        out=[]
        for i in range(min(10,await posts.count())):
            post=posts.nth(i)
            title_link=post.locator("a.submission__link").first
            if await title_link.count()==0:
                continue
            title=(await title_link.inner_text()).strip()
            permalink=None
            links=post.locator("a.text-sm")
            for j in range(await links.count()):
                href=await links.nth(j).get_attribute("href")
                if href and "/f/books/" in href:
                    permalink=href
                    break
            out.append({"rank":i+1,"title":title,"permalink":permalink})
        for row in out:
            href=row["permalink"]
            if not href:
                continue
            if href.startswith("/"):
                href=BASE+href
            detail=await ctx.new_page()
            resp=await detail.goto(href,wait_until="networkidle",timeout=120000)
            row["status"]=resp.status if resp else None
            row["url"]=detail.url
            submission=detail.locator(".submission").first
            if await submission.count()==0:
                raise RuntimeError(f"submission block missing for rank {row['rank']}")
            row["submission_text"]=(await submission.inner_text())[:12000]
            row["submission_html"]=(await submission.inner_html())[:24000]
            await detail.close()
        print(json.dumps(out,indent=2,ensure_ascii=False))
        await browser.close()

asyncio.run(main())
