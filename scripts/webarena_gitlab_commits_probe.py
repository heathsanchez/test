#!/usr/bin/env python3
import asyncio,json,re
from playwright.async_api import async_playwright
BASE="http://localhost:8023"
PATH="/a11yproject/a11yproject.com/-/commits/master"
def clean(s): return re.sub(r"\s+"," ",s).strip()
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(headless=True); page=await b.new_page()
    await page.goto(BASE+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze"); await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click(); await page.wait_for_url("**/",timeout=120000)
    r=await page.goto(BASE+PATH,wait_until="networkidle",timeout=180000)
    rows=[]
    for sel in [".commit",".commit-row","li.commit",".commits-list li"]:
      loc=page.locator(sel)
      if await loc.count():
        for i in range(min(40,await loc.count())):
          row=loc.nth(i)
          times=row.locator("time")
          rows.append({"selector":sel,"text":clean(await row.inner_text())[:2500],"html":(await row.inner_html())[:7000],"times":[{"datetime":await times.nth(j).get_attribute("datetime"),"text":clean(await times.nth(j).inner_text())} for j in range(await times.count())]})
        break
    links=await page.locator("a").evaluate_all("(els)=>els.filter(a=>(a.innerText||'').trim()==='Next'||(a.innerText||'').trim()==='2').slice(0,20).map(a=>({text:(a.innerText||'').trim(),href:a.href,class:a.className}))")
    print(json.dumps({"status":r.status if r else None,"url":page.url,"title":await page.title(),"rows":rows,"links":links,"body":(await page.locator("body").inner_text())[:16000]},indent=2,ensure_ascii=False))
    await b.close()
asyncio.run(main())
