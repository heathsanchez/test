#!/usr/bin/env python3
"""Intent-only Shopping category price-filter navigation."""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from urllib.parse import urlencode,urlparse,parse_qs
from playwright.async_api import async_playwright
from webarena_shopping_category_price_filter import resolve_category,ceiling

BASE="http://localhost:7770"

def parse_intent(intent):
    s=" ".join(str(intent).split())
    m=re.fullmatch(r'Open the "([^"]+)" category page filtered to under\s+\$?([0-9]+(?:\.[0-9]+)?)',s,re.I)
    if not m:
        raise ValueError(f"unsupported Shopping category filter intent: {intent!r}")
    return {"category":m.group(1),"price_cap":ceiling("under $"+m.group(2))}

async def navigate(page,parsed):
    selected,candidates=await resolve_category(page,BASE,parsed["category"])
    sep="&" if "?" in selected["href"] else "?"
    target=selected["href"]+sep+urlencode({"price":f'0-{parsed["price_cap"]}'})
    r=await page.goto(target,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200:
        raise RuntimeError(f"price-filter navigation failed {getattr(r,'status',None)}")
    observed=parse_qs(urlparse(page.url).query).get("price",[])
    if observed!=[f'0-{parsed["price_cap"]}']:
        raise RuntimeError("observed URL did not retain requested price filter")
    return {"capability":"category_price_ceiling","requested":parsed,
            "category_selected":selected,"category_candidates":candidates,
            "target":target,"observed_url":page.url}

async def run(intent,start_url,out):
    if start_url!="__SHOPPING__" and start_url!="http://localhost:7770":
        raise ValueError("category query requires Shopping start site")
    spec=parse_intent(intent)
    out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(record_har_path=str(out/"network.har"),record_har_mode="full")
        page=await ctx.new_page()
        try:
            evidence=await navigate(page,spec)
        finally:
            await ctx.close()
            await b.close()
    response={"task_type":"NAVIGATE","status":"SUCCESS",
              "retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--intent",required=True)
    ap.add_argument("--start-url",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))

if __name__=="__main__":
    main()
