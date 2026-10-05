#!/usr/bin/env python3
import asyncio,json,re
from playwright.async_api import async_playwright
BASE="http://localhost:7780/admin"
NAMES=["Sarah Miller","Jane Doe","Grace Nguyen","Alex Thomas","Lily Potter"]
def clean(s): return re.sub(r"\s+"," ",s).strip()
async def grid(page):
    for _ in range(100):
        ts=page.locator("table:visible")
        for i in range(await ts.count()):
            t=ts.nth(i); h=t.locator("thead th")
            hs=[clean(await h.nth(j).inner_text()).lower() for j in range(await h.count())]
            if {"id","purchase date","bill-to name","status"}.issubset(set(hs)) and await t.locator("tbody tr").count()>0:return t,hs
        await page.wait_for_timeout(100)
    raise RuntimeError("order grid missing")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page(); await page.goto(BASE+"/sales/order/",wait_until="networkidle",timeout=120000)
        t,hs=await grid(page); ix={k:hs.index(k) for k in ["id","purchase date","bill-to name","status"]}
        found={}; rows=t.locator("tbody tr")
        for i in range(await rows.count()):
            row=rows.nth(i); td=row.locator("td")
            if await td.count()<=max(ix.values()):continue
            name=clean(await td.nth(ix["bill-to name"]).inner_text()); status=clean(await td.nth(ix["status"]).inner_text()).lower()
            if name in NAMES and status=="pending" and name not in found:
                links=row.locator('a[href*="/sales/order/view/"]')
                found[name]={"display_id":clean(await td.nth(ix["id"]).inner_text()),"date":clean(await td.nth(ix["purchase date"]).inner_text()),"href":await links.first.get_attribute("href") if await links.count() else None}
        out={}; d=await ctx.new_page()
        for name,row in found.items():
            if not row["href"]:continue
            await d.goto(row["href"],wait_until="networkidle",timeout=120000)
            body=clean(await d.locator("body").inner_text()); low=body.lower(); pos=low.find("comments history")
            controls=[]
            loc=d.locator("input,textarea,select,button")
            for i in range(await loc.count()):
                e=loc.nth(i); namev=await e.get_attribute("name"); idv=await e.get_attribute("id"); textv=clean(await e.inner_text())
                key=((namev or "")+" "+(idv or "")+" "+textv).lower()
                if any(k in key for k in ["comment","notify","email","submit"]):
                    controls.append({"tag":await e.evaluate("(x)=>x.tagName"),"name":namev,"id":idv,"type":await e.get_attribute("type"),"disabled":await e.is_disabled(),"text":textv[:250],"value":await e.get_attribute("value")})
            out[name]={**row,"url":d.url,"excerpt":body[max(0,pos-500):pos+3000] if pos>=0 else body[:2500],"controls":controls}
        print(json.dumps(out,indent=2,ensure_ascii=False)); await b.close()
asyncio.run(main())
