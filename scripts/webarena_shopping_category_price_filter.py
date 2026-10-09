#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import urlparse, urlencode
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()
def tokens(s):
    stop={"with","and","the","for","of"}
    return [x for x in re.findall(r"[a-z0-9]+",clean(s).casefold()) if x not in stop]

def score(wanted,label,href):
    wt=tokens(wanted)
    path=urlparse(href).path
    path_tokens=tokens(path.replace("-"," "))
    hay=tokens(label+" "+path.replace("-"," "))
    overlap=sum(1 for w in wt if w in hay)
    exact=sum(1 for w in wt if w in hay)
    path_exact=sum(1 for w in wt if w in path_tokens)
    depth=len([x for x in path.split("/") if x])
    category_bonus=2 if path.endswith(".html") and depth>=2 else 0
    # Parent breadcrumbs are shared by siblings; prefer the actual leaf
    # category's label or slug when both resolve to the same ancestor.
    leaf=path.rsplit("/",1)[-1].removesuffix(".html").replace("-"," ")
    direct=set(tokens(label+" "+leaf))
    leaf_matches=sum(1 for word in wt if word in direct)
    return overlap*5+exact*2+path_exact*8+category_bonus+leaf_matches*12

def ceiling(spec):
    m=re.search(r"under\s*\$?([0-9]+(?:\.[0-9]+)?)",clean(spec),re.I)
    if not m: raise ValueError(f"unsupported price range: {spec}")
    return m.group(1)

async def resolve_category(page,base,wanted):
    r=await page.goto(base,wait_until="networkidle",timeout=120000)
    if r is None or r.status not in (200,302): raise RuntimeError("shopping home failed")
    anchors=page.locator('a[href]')
    rows=[]; seen=set()
    for i in range(await anchors.count()):
        a=anchors.nth(i)
        href=await a.get_attribute("href")
        if not href or ".html" not in href: continue
        if href.startswith("/"): href=base+href
        if not href.startswith(base): continue
        if href in seen: continue
        seen.add(href)
        label=clean(await a.inner_text())
        sc=score(wanted,label,href)
        if sc>0: rows.append({"score":sc,"label":label,"href":href})
    rows.sort(key=lambda x:(-x["score"],-len([p for p in urlparse(x["href"]).path.split("/") if p]),x["href"]))
    if not rows or rows[0]["score"]<7:
        raise RuntimeError(f"no category candidate for {wanted!r}: {rows[:10]}")
    return rows[0],rows[:10]

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=139: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    wanted=str(inst["product_category"]); cap=ceiling(str(inst["price_range"])); base=a.base_url.rstrip("/")
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        chosen,candidates=await resolve_category(page,base,wanted)
        sep="&" if "?" in chosen["href"] else "?"
        target=chosen["href"]+sep+urlencode({"price":f"0-{cap}"})
        r=await page.goto(target,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"filtered category failed: {target}")
        final=page.url
        await ctx.close(); await browser.close()
    response={"task_type":"NAVIGATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"wanted":wanted,"price_cap":cap,"chosen":chosen,"candidates":candidates,"target":target,"final_url":final}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
