#!/usr/bin/env python3
from __future__ import annotations
import asyncio, json
from playwright.async_api import async_playwright

BASE="http://localhost:9999"
AUTH={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"}

async def describe(page,path):
    r=await page.goto(BASE+path,wait_until="networkidle",timeout=120000)
    forms=[]
    loc=page.locator("form")
    for i in range(await loc.count()):
        form=loc.nth(i)
        controls=[]
        cs=form.locator("input,textarea,select,button")
        for j in range(await cs.count()):
            el=cs.nth(j)
            controls.append({
                "tag":await el.evaluate("(e)=>e.tagName.toLowerCase()"),
                "name":await el.get_attribute("name"),
                "id":await el.get_attribute("id"),
                "type":await el.get_attribute("type"),
                "value":(await el.get_attribute("value")),
                "text":(await el.inner_text())[:200] if await el.evaluate("(e)=>['button','textarea','select'].includes(e.tagName.toLowerCase())") else None,
            })
        forms.append({
            "action":await form.get_attribute("action"),
            "method":await form.get_attribute("method"),
            "controls":controls,
            "html":(await form.inner_html())[:8000],
        })
    return {
        "path":path,
        "status":r.status if r else None,
        "final_url":page.url,
        "title":await page.title(),
        "forms":forms,
        "body":(await page.locator("body").inner_text())[:12000],
    }

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH)
        page=await ctx.new_page()
        out=[]
        for path in ["/submit/iphone","/submit","/f/iphone","/"]:
            try: out.append(await describe(page,path))
            except Exception as e: out.append({"path":path,"error":repr(e),"final_url":page.url})
        await b.close()
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
