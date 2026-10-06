#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

PRODUCTS=[
 "Alaffia Everyday Shea Conditioner, Lavender, 32 Oz. Moisturizes, Restores and Protects. Made with Fair Trade Shea Butter, Cruelty Free, No Parabens, Vegan.",
 "Revlon Colorsilk Haircolor, Medium Blonde, 10 Ounces (Pack of 3)",
 "Bornbridge Artificial Spiral Topiary Tree - Indoor / Outdoor Topiary Trees - Artificial Outdoor Plants (2 Pack, 4' Cypress)",
]

def norm(s): return re.sub(r"\s+"," ",str(s)).strip().casefold()

async def gql(page,base,search):
    query="""query($search:String!){products(search:$search,pageSize:50){items{sku name categories{id name path url_path}}}}"""
    payload=await page.evaluate("""async ({url,query,search}) => {
      const r=await fetch(url+'/graphql',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({query,variables:{search}})});
      return {status:r.status,text:await r.text()};
    }""",{"url":base.rstrip("/"),"query":query,"search":search})
    if payload["status"]!=200: raise RuntimeError(payload)
    return json.loads(payload["text"])

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--base-url",default="http://localhost:7770"); ap.add_argument("--output",required=True); a=ap.parse_args()
    out={}
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await page.goto(a.base_url.rstrip("/"),wait_until="networkidle",timeout=120000)
        for name in PRODUCTS:
            data=await gql(page,a.base_url,name)
            items=data.get("data",{}).get("products",{}).get("items",[])
            exact=next((x for x in items if norm(x.get("name"))==norm(name)),None)
            out[name]={"exact":exact,"candidates":items[:10]}
        await b.close()
    Path(a.output).write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__": asyncio.run(main())
