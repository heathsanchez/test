#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from decimal import Decimal
from pathlib import Path
from playwright.async_api import async_playwright
import webarena_shopping_category_spend as base

def norm(s):
    s=str(s).casefold().replace("&"," and ")
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def category_tokens(s):
    stop={"and","the","of","for"}
    return [x for x in norm(s).split() if x not in stop]

def category_match(wanted,categories):
    wt=category_tokens(wanted)
    wanted_norm=norm(wanted)
    names=[norm(c.get("name","")) for c in categories]
    # Accessory descendants are a merchandising side branch, not functional
    # membership in a parent-category query unless the user asks for them.
    if "accessor" not in wanted_norm and any("accessor" in name for name in names):
        return False
    for c in categories:
        hay=norm(" ".join(str(c.get(k,"")) for k in ("name","path","url_path")))
        ht=hay.split()
        if wt and all(any(w==h or w in h or h in w for h in ht) for w in wt):
            return True
    # Conjoined category language can name a parent function with a stylistic
    # synonym (e.g. "hair care and hair style"). Preserve the parent match
    # when the stable leading category concept is present.
    if len(wt)>=2:
        head=wt[:2]
        for c in categories:
            ht=norm(c.get("name","")).split()
            if all(any(w==h or w in h or h in w for h in ht) for w in head):
                return True
    return False

async def product_categories(page,base_url,name):
    query="""query($search:String!){products(search:$search,pageSize:50){items{name sku categories{id name path url_path}}}}"""
    payload=await page.evaluate("""async ({url,query,search}) => {
      const r=await fetch(url+'/graphql',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({query,variables:{search}})});
      return {status:r.status,text:await r.text()};
    }""",{"url":base_url.rstrip("/"),"query":query,"search":name})
    if payload["status"]!=200:
        raise RuntimeError(f"graphql failed {payload['status']}")
    items=json.loads(payload["text"]).get("data",{}).get("products",{}).get("items",[])
    exact=next((x for x in items if norm(x.get("name",""))==norm(name)),None)
    if exact is None:
        ranked=sorted(items,key=lambda x:base.product_match(name,x.get("name","")),reverse=True)
        exact=ranked[0] if ranked and base.product_match(name,ranked[0].get("name","")) else None
    if exact is None:
        raise RuntimeError(f"product not resolved: {name}")
    return exact

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=162:
        raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    category=base.clean(inst["category"])
    time_spec=base.parse_time(inst["time"])
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=base.AUTH_HEADER)
        page=await ctx.new_page()
        await page.goto(a.base_url.rstrip("/"),wait_until="networkidle",timeout=120000)
        orders=await base.order_rows(page,a.base_url)
        relevant=[o for o in orders if base.in_time(o["date"],time_spec)]
        total=Decimal("0"); evidence_rows=[]
        for order in relevant:
            for item in await base.items(page,order):
                product=await product_categories(page,a.base_url,item["name"])
                cats=product.get("categories") or []
                keep=category_match(category,cats)
                evidence_rows.append({
                    "order_no":order["order_no"],
                    "date":order["date"].date().isoformat(),
                    "name":item["name"],
                    "subtotal":str(item["subtotal"]),
                    "categories":cats,
                    "included":keep,
                })
                if keep:
                    total+=item["subtotal"]
        await b.close()
    total=total.quantize(Decimal("0.01"))
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[float(total)],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    ev={"task_id":a.task_id,"category":category,"orders_in_period":len(relevant),"items":evidence_rows,"total":str(total)}
    (out/"capability_evidence.json").write_text(json.dumps(ev,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(ev,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
