#!/usr/bin/env python3
"""Prospective two-capability source-pinned WebArena composition test.

Previously independently qualified:
 E: grouped-row-count/customer-email (2026-10-07).
 F: cancellation filter on grouped customer orders (2026-10-10).
Train exclusively task 288; freeze *all* candidate arms before touching 292/290.
Novel task 290 additionally demands opening source UI order-detail/SKU evidence.
No task evaluator/reference data are accessible to candidate construction.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import webarena_compounding_economics_v1 as prev

E_FREEZE = "66930dc2ea50b944564c46e12d531b6daca8d609cb2495b21152078a3c87267d"
SOURCE = "6473f72db5dcefc97b5725b59e734504edc28a21"
TRAIN = 288
FUTURE = (292, 290)
STATUS = ("any", "complete", "cancelled")

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verdict(ok):
    return "WARRANTED_BOUNDED" if ok else "UNKNOWN"

def passed(s):
    return s["score"] == 1.0 and s["status"] == "success"

def verify_sources(root):
    e, ereceipt = prev.verify_retained(root / "e_archive")
    f = read(root / "f_archive" / "result.json")
    assert f["authority_commit"] == SOURCE
    assert f["prior_e"]["freeze_sha256"] == E_FREEZE
    assert f["claims"]["reusable_E_to_F_cancellation_grouping"] == "WARRANTED_BOUNDED"
    assert f["arms"]["retained_e"]["state"] == "WARRANTED_BOUNDED_F"
    chosen = f["arms"]["retained_e"]["chosen"]
    assert chosen == {"group_key":"customer email","status_filter":"cancelled"}
    assert f["arms"]["retained_e"]["heldout_results"] and all(
        passed(a) for a in f["arms"]["retained_e"]["heldout_results"])
    return e, chosen, {"e":ereceipt, "f_result_sha256":sha(root/"f_archive"/"result.json"),
                       "f_training":f["train"],"f_heldout":f["heldout"],
                       "f_original_acquisition_evaluations":f["arms"]["retained_e"]["candidate_task_evaluations"]}

def status_from_intent(intent):
    low = intent.lower()
    # Strong stateless comparison: generic language-to-filter inference, no historical memory.
    if "cancellation" in low or "cancelled" in low or "canceled" in low:
        return "cancelled"
    if "complete" in low: return "complete"
    return "any"

def options(task, obs, e, f):
    strong_key = prev.infer_schema_key(task["intent"], obs)
    strong_status = status_from_intent(task["intent"])
    keys = prev.candidate_keys(obs)
    assert e["group_key"] == strong_key and strong_status == f["status_filter"]
    # Every arm uses the identical candidate evaluator and observation; only admitted
    # prior *verified* distinctions differ. Order is fixed before training.
    return {
        "retain_both": ([e["group_key"]], [f["status_filter"]]),
        "ablate_E_grouping": (keys, [f["status_filter"]]),
        "ablate_F_filter": ([e["group_key"]], list(STATUS)),
        "ablate_both": (keys, list(STATUS)),
        "strong_stateless": ([strong_key], [strong_status]),
    }

def score(wa, empty, root, arm, phase, task_id, response):
    out = root / "candidate_responses" / arm / phase
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{task_id}.json"
    path.write_text(json.dumps(response, indent=2)+"\n")
    t=time.perf_counter()
    verdict=wa.evaluate_task(task_id=task_id, agent_response=path, network_trace=empty)
    return {"score":float(verdict.score),"status":verdict.status.value,
            "verifier_seconds":round(time.perf_counter()-t,6),
            "response_sha256":sha(path)}

def candidate(root, wa, empty, ob, budget, options_by_arm):
    arms={}
    for arm,(keys,filters) in options_by_arm.items():
        history=[]
        winner=None
        t=time.perf_counter()
        for key in keys:
            for filt in filters:
                if len(history)>=budget: break
                response=prev.response_for(TRAIN,ob,key,filt)
                entry=score(wa,empty,root,arm,"train",TRAIN,response)
                entry.update({"key":key,"status_filter":filt})
                history.append(entry)
                if passed(entry):
                    winner={"group_key":key,"status_filter":filt}
                    break
            if winner or len(history)>=budget: break
        frozen={
            "arm":arm, "winner":winner, "train_task":TRAIN,
            "history":[{k:v for k,v in h.items() if k in ("key","status_filter","score","status")} for h in history],
            "source":"pinned_web_arena_official_verifier",
        }
        frozen["sha256"]=prev.digest(frozen)
        (root/f"{arm}_freeze.json").write_text(json.dumps(frozen,indent=2)+"\n")
        arms[arm]={"winner":winner,"search_log":history,"candidate_evaluations":len(history),
                   "candidate_verifier_seconds":sum(v["verifier_seconds"] for v in history),
                   "search_wall_seconds":round(time.perf_counter()-t,6),
                   "freeze_sha256":frozen["sha256"],"state":"FROZEN_BEFORE_FUTURE"}
    return arms

def parse_date(raw):
    from dateutil.parser import parse
    return parse(raw, fuzzy=False)

async def observe_order_skus(base_url, email, observation):
    """Independently observe the actual Magento order grid and detail page."""
    from playwright.async_api import async_playwright
    from webarena_customer_count_representation_synth import (
        expose_customer_email, live_table, advance)
    from webarena_shopping_admin_customer_order_counts import rewind_first
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        try:
            r=await page.goto(base_url.rstrip("/")+"/sales/order/",wait_until="networkidle",timeout=120000)
            if r is None or r.status!=200: raise RuntimeError("order grid response not 200")
            await expose_customer_email(page)
            await rewind_first(page)
            selected=[]
            seen=set()
            for _ in range(50):
                tab,hs=await live_table(page)
                lower=[h.lower() for h in hs]
                needed=("id","customer email","status","purchase date")
                assert set(needed).issubset(set(lower)), lower
                ix={x:lower.index(x) for x in needed}
                rows=tab.locator("tbody tr")
                for n in range(await rows.count()):
                    row=rows.nth(n)
                    cells=row.locator("td")
                    if await cells.count()<=max(ix.values()):continue
                    oid=(await cells.nth(ix["id"]).inner_text()).strip()
                    if oid in seen:continue
                    seen.add(oid)
                    em=(await cells.nth(ix["customer email"]).inner_text()).strip()
                    st=(await cells.nth(ix["status"]).inner_text()).strip().lower()
                    if em.casefold()!=email.casefold() or st not in ("canceled","cancelled"):continue
                    stamp=(await cells.nth(ix["purchase date"]).inner_text()).strip()
                    lk=row.locator('a[href*="/sales/order/view/"]')
                    href=await lk.first.get_attribute("href") if await lk.count() else None
                    selected.append({"order_id":oid,"purchase_date":stamp,"href":href})
                if not await advance(page,tab,hs):break
            if not selected:raise RuntimeError("no source-visible cancelled orders for selected customer")
            ordered=sorted(selected,key=lambda x:(parse_date(x["purchase_date"]),int(x["order_id"])),reverse=True)
            first=ordered[0]
            if not first["href"]:raise RuntimeError("no order view link; cannot infer detail from source")
            d=await page.goto(first["href"],wait_until="networkidle",timeout=120000)
            if d is None or d.status!=200:raise RuntimeError("order detail unavailable")
            table=page.locator("table.edit-order-table")
            if not await table.count():raise RuntimeError("order item table missing")
            table=table.first
            th=table.locator("thead th")
            headers=[(await th.nth(i).inner_text()).strip().lower() for i in range(await th.count())]
            if "product" not in headers:raise RuntimeError(f"product column unavailable: {headers}")
            ix=headers.index("product")
            result=[]
            tr=table.locator("tbody tr")
            for i in range(await tr.count()):
                cells=tr.nth(i).locator("td")
                if await cells.count()<=ix:continue
                txt=(await cells.nth(ix).inner_text()).strip()
                m=re.search(r"SKU\s*:\s*([A-Za-z0-9][\w.-]*)",txt,re.I)
                if m:result.append(m.group(1))
            if not result:raise RuntimeError("no source-visible SKUs in latest cancelled order")
            return {"selected_customer":email,"source_order":first,
                    "cancelled_orders_for_customer":len(selected),
                    "sku_count":len(result),"skus":result}
        finally:await browser.close()

def select_winners(obs,key,status):
    from collections import Counter
    rows = obs["rows"] if status=="any" else [r for r in obs["rows"] if r["status_class"]==status]
    counts=Counter(r[key] for r in rows)
    if not counts:return []
    best=max(counts.values())
    return sorted(k for k,v in counts.items() if v==best)

def selftest():
    ob={"row_semantics":"one row per order","rows":[
        {"id":"1","customer email":"alice","status_class":"cancelled"},
        {"id":"2","customer email":"alice","status_class":"cancelled"},
        {"id":"3","customer email":"bob","status_class":"complete"}]}
    assert select_winners(ob,"customer email","cancelled")==["alice"]
    assert status_from_intent("customer with most cancellations")=="cancelled"
    assert options({"intent":"Get the email of the customer with the most cancellations"},
                   ob,{"group_key":"customer email"},{"status_filter":"cancelled"})["strong_stateless"]==(
                       ["customer email"],["cancelled"])
    assert prev.response_for(292,ob,"customer email","cancelled")["retrieved_data"]==[2]
    print("SELFTEST_OK")

def main(args):
    from webarena_verified.api import WebArenaVerified
    from webarena_verified.types.config import WebArenaVerifiedConfig
    from webarena_verified.types.tracing import NetworkTrace
    root=Path(args.root)
    root.mkdir(parents=True,exist_ok=True)
    e,f,receipt=verify_sources(root)
    tasks=prev.validate_input(read(args.tasks),read(args.observation))
    assert int(tasks[TRAIN]["intent_template_id"])==234
    assert all(int(tasks[k]["intent_template_id"])==234 for k in FUTURE)
    assert all("eval" not in item and "reference_url" not in item for item in read(args.tasks))
    ob=read(args.observation)
    wa=WebArenaVerified(config=WebArenaVerifiedConfig.from_file(Path(args.config)))
    empty=NetworkTrace.model_construct(is_playwright=False,src_file=Path("<none>"),events=())
    hypothesis=options(tasks[TRAIN],ob,e,f)
    arms=candidate(root,wa,empty,ob,args.budget,hypothesis)
    # All acquisition arms frozen before inspecting either heldout task.
    assert all((root/f"{name}_freeze.json").exists() for name in hypothesis)
    assert arms["retain_both"]["winner"]=={"group_key":"customer email","status_filter":"cancelled"}
    detail=None
    detail_error=None
    # All arms share the same independently acquired SOURCE observation; no candidate
    # may inspect task 290 expected answer or evaluator metadata.
    try:
        winners=select_winners(ob,"customer email","cancelled")
        if len(winners)!=1:raise RuntimeError(f"ambiguous top cancelled customer: {len(winners)}")
        detail=asyncio.run(observe_order_skus(args.base_url,winners[0],ob))
    except Exception as e:
        detail_error=f"{type(e).__name__}: {str(e)[:400]}"
    if detail is not None:
        (root/"source_detail.json").write_text(json.dumps(detail,indent=2)+"\n")
    for name,arm in arms.items():
        w=arm["winner"]
        held=[]
        if w:
            held.append(dict(task_id=292, **score(wa,empty,root,name,"future",292,
                           prev.response_for(292,ob,w["group_key"],w["status_filter"]))))
            if detail is not None:
                actual_winners=select_winners(ob,w["group_key"],w["status_filter"])
                if actual_winners==[detail["selected_customer"]]:
                    resp={"task_type":"RETRIEVE","status":"SUCCESS",
                          "retrieved_data":detail["skus"],"error_details":None}
                    held.append(dict(task_id=290,**score(wa,empty,root,name,"future",290,resp)))
                else:
                    held.append({"task_id":290,"state":"UNSUPPORTED_CANDIDATE_WITNESS"})
        arm["future"]=held
        arm["state"]="WARRANTED_BOUNDED_COMPOSITION" if (
            {h.get("task_id") for h in held}==set(FUTURE) and
            all("score" in h and passed(h) for h in held)) else "UNKNOWN_OR_REJECTED_COMPOSITION"
    both=arms["retain_both"]
    strong=arms["strong_stateless"]
    successful=both["state"]=="WARRANTED_BOUNDED_COMPOSITION"
    stateless_ok=strong["state"]=="WARRANTED_BOUNDED_COMPOSITION"
    report={
        "objective":"Two independently qualified E grouping and F cancellation filter compositional reuse",
        "source_authority":SOURCE,"e_f_receipts":receipt,
        "candidate_data_sha256":sha(args.tasks),
        "fresh_observation_sha256":sha(args.observation),
        "train_task":TRAIN,"future_tasks":list(FUTURE),
        "budget_per_arm":args.budget,"arms":arms,
        "source_detail_error":detail_error,
        "claims":{
            "prospective_two_capability_composition":{"state":verdict(successful)},
            "E_ablation_causal_candidate_cost":{
                "state":verdict(successful and arms["ablate_E_grouping"]["candidate_evaluations"]>both["candidate_evaluations"])},
            "F_ablation_causal_candidate_cost":{
                "state":verdict(successful and arms["ablate_F_filter"]["candidate_evaluations"]>both["candidate_evaluations"])},
            "strict_candidate_cost_benefit_over_strong_stateless":{
                "state":"WARRANTED_BOUNDED" if successful and stateless_ok and
                both["candidate_evaluations"]<strong["candidate_evaluations"] else
                "REJECTED_ON_THIS_CASE" if successful and stateless_ok else "UNKNOWN"},
            "full_amortized_recursive_acceleration":{"state":"UNKNOWN"},
        }}
    (root/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"claims":report["claims"],"detail_error":detail_error,
           "arms":{k:{"candidate_evaluations":v["candidate_evaluations"],"state":v["state"],
                      "future":v["future"]} for k,v in arms.items()}},indent=2))
    assert len(arms)==5 and all(v["candidate_evaluations"]<=args.budget for v in arms.values())

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--root",default="artifacts/two_capability_composition_v1")
    ap.add_argument("--tasks",default="artifacts/two_capability_composition_v1/full_no_eval.json")
    ap.add_argument("--config",default="artifacts/two_capability_composition_v1/config.json")
    ap.add_argument("--observation",default="artifacts/two_capability_composition_v1/observation.json")
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--budget",type=int,default=12)
    args=ap.parse_args()
    if args.self_test:selftest()
    else:main(args)
