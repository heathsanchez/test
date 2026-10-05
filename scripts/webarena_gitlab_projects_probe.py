#!/usr/bin/env python3
import asyncio, json
from playwright.async_api import async_playwright

BASE="http://localhost:8023"

async def login(page):
    await page.goto(BASE+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/",timeout=120000)

async def snap(page,path):
    r=await page.goto(BASE+path,wait_until="networkidle",timeout=180000)
    links=await page.locator("a").evaluate_all("(els)=>els.slice(0,250).map(a=>({text:(a.innerText||'').trim(),href:a.href,class:a.className}))")
    return {"path":path,"status":r.status if r else None,"url":page.url,"title":await page.title(),"body":(await page.locator("body").inner_text())[:30000],"links":links}

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context()
        page=await ctx.new_page()
        await login(page)
        out=[]
        for path in ["/byteblaze","/dashboard/projects","/users/byteblaze/projects","/explore/projects"]:
            try:
                out.append(await snap(page,path))
            except Exception as e:
                out.append({"path":path,"error":str(e)})
        print(json.dumps(out,indent=2,ensure_ascii=False))
        await browser.close()

asyncio.run(main())
