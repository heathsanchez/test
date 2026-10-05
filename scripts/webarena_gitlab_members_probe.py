#!/usr/bin/env python3
import asyncio, json, re
from urllib.parse import quote
from playwright.async_api import async_playwright

BASE="http://localhost:8023"

async def login(page):
    await page.goto(BASE+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/",timeout=120000)

async def resolve(page,wanted):
    await page.goto(f"{BASE}/search?search={quote(wanted)}&scope=projects",wait_until="networkidle",timeout=180000)
    links=page.locator("a")
    for i in range(await links.count()):
        a=links.nth(i)
        href=await a.get_attribute("href")
        txt=(await a.inner_text()).strip()
        if href and wanted.casefold() in (txt+" "+href).casefold():
            m=re.search(r"(/[^/?#]+/[^/?#]+)",href)
            if m: return m.group(1)
    raise RuntimeError("project not resolved")

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        await login(page)
        out=[]
        for wanted in ("gimmiethat.space","prism-theme"):
            path=await resolve(page,wanted)
            item={"wanted":wanted,"project_path":path,"attempts":[]}
            for suffix in ("/-/project_members","/-/settings/members","/project_members"):
                r=await page.goto(BASE+path+suffix,wait_until="networkidle",timeout=180000)
                body=(await page.locator("body").inner_text())[:30000]
                links=await page.locator("a").evaluate_all("(els)=>els.slice(0,400).map(a=>({text:(a.innerText||'').trim(),href:a.getAttribute('href'),testid:a.getAttribute('data-testid'),cls:a.className}))")
                rows=await page.locator("tr, li, [data-testid*=member], [class*=member]").evaluate_all("(els)=>els.slice(0,250).map(e=>({tag:e.tagName,text:(e.innerText||'').trim().slice(0,1000),testid:e.getAttribute('data-testid'),cls:e.className}))")
                item["attempts"].append({"suffix":suffix,"status":r.status if r else None,"url":page.url,"body":body,"links":links,"rows":rows})
            out.append(item)
        print(json.dumps(out,indent=2,ensure_ascii=False))
        await browser.close()

asyncio.run(main())
