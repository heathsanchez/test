#!/usr/bin/env python3
"""Schema-driven temporal event-count representation synthesis.

This generator does not use the earlier fixed relation-operator library or the
grouped-count representation from capability E. From a no-answer task corpus
and an observed GitLab commit schema it generates candidate role bindings for:
  entity identity -> record field
  event time      -> timestamp field
then compiles a new representation:
  filter(entity) -> filter(time in task-derived interval) -> count(events)

Role candidates are generated from observed values/types rather than a
hand-listed domain candidate menu.
"""
from __future__ import annotations

import argparse
import asyncio
import calendar
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, quote

from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE, sign_in


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def month_num(token: str) -> int:
    t = token.strip().lower().rstrip(".")
    for i in range(1, 13):
        if t in {calendar.month_name[i].lower(), calendar.month_abbr[i].lower()}:
            return i
    raise ValueError(token)


def parse_iso_time(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        v = value.replace("Z", "+00:00")
        d = datetime.fromisoformat(v)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def parse_period(text: str) -> tuple[datetime, datetime, dict]:
    s = clean(text)

    m = re.fullmatch(r"during\s+(\d{4})", s, re.I)
    if m:
        y = int(m.group(1))
        a, b = datetime(y,1,1,tzinfo=timezone.utc), datetime(y+1,1,1,tzinfo=timezone.utc)
        return a,b,{"kind":"year","year":y}

    m = re.fullmatch(r"in\s+([A-Za-z]+)\s+(\d{4})", s, re.I)
    if m:
        mon, y = month_num(m.group(1)), int(m.group(2))
        a = datetime(y,mon,1,tzinfo=timezone.utc)
        b = datetime(y+1,1,1,tzinfo=timezone.utc) if mon==12 else datetime(y,mon+1,1,tzinfo=timezone.utc)
        return a,b,{"kind":"month","year":y,"month":mon}

    m = re.fullmatch(
        r"between\s+start\s+of\s+([A-Za-z]+)\s+(\d{4})\s+and\s+end\s+of\s+([A-Za-z]+)\s+(\d{4})",
        s,re.I,
    )
    if m:
        sm,sy,em,ey=m.groups()
        sm,sy,em,ey=month_num(sm),int(sy),month_num(em),int(ey)
        a=datetime(sy,sm,1,tzinfo=timezone.utc)
        b=datetime(ey+1,1,1,tzinfo=timezone.utc) if em==12 else datetime(ey,em+1,1,tzinfo=timezone.utc)
        return a,b,{"kind":"month_range","start":[sy,sm],"end":[ey,em]}

    m = re.fullmatch(
        r"between\s+([A-Za-z]+)\s+(\d{4})\s+through\s+([A-Za-z]+)\s+(\d{4})",
        s,re.I,
    )
    if m:
        sm,sy,em,ey=m.groups()
        sm,sy,em,ey=month_num(sm),int(sy),month_num(em),int(ey)
        a=datetime(sy,sm,1,tzinfo=timezone.utc)
        b=datetime(ey+1,1,1,tzinfo=timezone.utc) if em==12 else datetime(ey,em+1,1,tzinfo=timezone.utc)
        return a,b,{"kind":"month_range","start":[sy,sm],"end":[ey,em]}

    m = re.fullmatch(r"on\s+([A-Za-z]+)\s+(\d+)(?:st|nd|rd|th)?\s+(\d{4})", s, re.I)
    if m:
        mon,day,y=month_num(m.group(1)),int(m.group(2)),int(m.group(3))
        a=datetime(y,mon,day,tzinfo=timezone.utc)
        return a,a+timedelta(days=1),{"kind":"day","year":y,"month":mon,"day":day}

    raise ValueError(f"unsupported period syntax: {text!r}")


def load_tasks(path: str) -> list[dict]:
    return json.loads(Path(path).read_text())


def get_task(tasks: list[dict], task_id: int) -> dict:
    t = next(x for x in tasks if int(x["task_id"]) == task_id)
    if int(t["intent_template_id"]) != 321:
        raise SystemExit(f"task {task_id} is not template 321")
    return t


async def fetch_all_commits(page, repo_path: str) -> list[dict]:
    project_id = quote(repo_path.strip("/"), safe="")
    out=[]
    seen=set()
    for pageno in range(1, 100):
        api=f"{BASE}/api/v4/projects/{project_id}/repository/commits?ref_name=main&per_page=100&page={pageno}"
        payload=await page.evaluate(
            """async (url) => {
                const r = await fetch(url, {credentials:'same-origin'});
                return {status:r.status, text:await r.text()};
            }""",
            api,
        )
        if payload["status"] != 200:
            raise RuntimeError(f"GitLab commits API failed: {payload['status']} {payload['text'][:500]}")
        data=json.loads(payload["text"])
        if not data:
            break
        for item in data:
            sha=item.get("id") or item.get("short_id")
            if not sha or sha in seen:
                continue
            seen.add(sha)
            out.append(item)
        if len(data) < 100:
            break
    if not out:
        raise RuntimeError("no commits observed")
    return out


async def observe(task_file: str, task_id: int, output: str) -> None:
    tasks=load_tasks(task_file)
    task=get_task(tasks,task_id)
    start_url=task["start_urls"][0].replace("__GITLAB__",BASE)
    repo_path=urlparse(start_url).path.rstrip("/")
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        page=await b.new_page()
        await sign_in(page)
        records=await fetch_all_commits(page,repo_path)
        await b.close()
    scalar_fields={}
    keys=sorted({k for r in records for k,v in r.items() if isinstance(v,(str,int,float,bool)) or v is None})
    for k in keys:
        vals=[r.get(k) for r in records]
        scalar_fields[k]={
            "non_null":sum(v is not None for v in vals),
            "string":sum(isinstance(v,str) for v in vals),
            "parseable_time":sum(parse_iso_time(v) is not None for v in vals if isinstance(v,str)),
        }
    data={"repo_path":repo_path,"record_count":len(records),"scalar_fields":scalar_fields,"records":records}
    pth=Path(output); pth.parent.mkdir(parents=True,exist_ok=True); pth.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({"repo_path":repo_path,"record_count":len(records),"fields":scalar_fields},indent=2))


def candidate_entity_fields(records: list[dict], training_tasks: list[dict]) -> list[str]:
    wanted=[clean(str(t["instantiation_dict"]["user"])).casefold() for t in training_tasks]
    keys=sorted({k for r in records for k,v in r.items() if isinstance(v,str)})
    scored=[]
    for k in keys:
        hits=0
        for w in wanted:
            if any(
                isinstance(r.get(k),str)
                and (clean(r[k]).casefold()==w or clean(r[k]).casefold().startswith(w+" "))
                for r in records
            ):
                hits += 1
        if hits:
            scored.append((hits,k))
    if not scored:
        raise RuntimeError("no observed string field contains training entity values")
    best=max(x[0] for x in scored)
    return [k for hits,k in scored if hits==best]


def candidate_time_fields(records: list[dict]) -> list[str]:
    keys=sorted({k for r in records for k,v in r.items() if isinstance(v,str)})
    scored=[]
    for k in keys:
        vals=[r.get(k) for r in records if isinstance(r.get(k),str)]
        if not vals:
            continue
        n=sum(parse_iso_time(v) is not None for v in vals)
        if n:
            scored.append((n/len(vals),n,k))
    if not scored:
        raise RuntimeError("no parseable timestamp fields")
    best=max(x[0] for x in scored)
    return [k for ratio,n,k in scored if ratio==best and ratio>=0.8]


def generate_representations(task_file: str, training_ids: list[int], observation_path: str, output: str) -> None:
    tasks=load_tasks(task_file)
    train=[get_task(tasks,i) for i in training_ids]
    obs=json.loads(Path(observation_path).read_text())
    records=obs["records"]

    if not all(str(t["intent"]).casefold().startswith("how many commits did ") for t in train):
        raise RuntimeError("training residuals do not expose event-count structure")
    for t in train:
        parse_period(str(t["instantiation_dict"]["period"]))

    entities=candidate_entity_fields(records,train)
    times=candidate_time_fields(records)
    reps=[]
    for ef in entities:
        for tf in times:
            reps.append({
                "representation_type":"temporal_windowed_entity_event_count",
                "entity_field":ef,
                "time_field":tf,
                "measure":"row_count",
                "window_semantics":"half_open_utc_interval",
                "induced_from":{
                    "training_ids":training_ids,
                    "entity_role_evidence":"training slot values occur in observed string field",
                    "time_role_evidence":"observed field values parse as timestamps",
                    "measure_evidence":"How many <events> question form",
                },
            })
    if not reps:
        raise RuntimeError("no representation candidates generated")
    p=Path(output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(reps,indent=2)+"\n")
    print(json.dumps({"candidate_count":len(reps),"entity_fields":entities,"time_fields":times},indent=2))


def entity_match(observed: str, wanted: str) -> bool:
    a=clean(observed).casefold(); b=clean(wanted).casefold()
    return a==b or a.startswith(b+" ")


def execute(task: dict, observation: dict, representation: dict, ablate_window: bool=False) -> tuple[dict,dict]:
    records=observation["records"]
    ef=representation["entity_field"]; tf=representation["time_field"]
    user=str(task["instantiation_dict"]["user"])
    start,end,window=parse_period(str(task["instantiation_dict"]["period"]))
    entity_rows=[r for r in records if isinstance(r.get(ef),str) and entity_match(r[ef],user)]
    if ablate_window:
        chosen=entity_rows
    else:
        chosen=[]
        for r in entity_rows:
            dt=parse_iso_time(r.get(tf))
            if dt is not None and start <= dt < end:
                chosen.append(r)
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[len(chosen)],"error_details":None}
    evidence={
        "representation":representation,
        "user":user,
        "window":{"start":start.isoformat(),"end_exclusive":end.isoformat(),**window},
        "entity_row_count":len(entity_rows),
        "selected_row_count":len(chosen),
        "ablate_window":ablate_window,
    }
    return response,evidence


def compute(task_file: str, task_id: int, observation_path: str, representation_path: str, output_dir: str, ablate_window: bool) -> None:
    tasks=load_tasks(task_file); task=get_task(tasks,task_id)
    obs=json.loads(Path(observation_path).read_text())
    rep=json.loads(Path(representation_path).read_text())
    response,evidence=execute(task,obs,rep,ablate_window)
    out=Path(output_dir)/str(task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"task_id":task_id,**evidence},indent=2)+"\n")
    print(json.dumps({"task_id":task_id,"response":response,"evidence":evidence},indent=2))


async def main() -> None:
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)

    o=sub.add_parser("observe")
    o.add_argument("--task-file",required=True)
    o.add_argument("--task-id",type=int,required=True)
    o.add_argument("--output",required=True)

    g=sub.add_parser("generate")
    g.add_argument("--task-file",required=True)
    g.add_argument("--training-ids",required=True)
    g.add_argument("--observation",required=True)
    g.add_argument("--output",required=True)

    c=sub.add_parser("compute")
    c.add_argument("--task-file",required=True)
    c.add_argument("--task-id",type=int,required=True)
    c.add_argument("--observation",required=True)
    c.add_argument("--representation",required=True)
    c.add_argument("--output-dir",required=True)
    c.add_argument("--ablate-window",action="store_true")

    args=ap.parse_args()
    if args.cmd=="observe":
        await observe(args.task_file,args.task_id,args.output)
    elif args.cmd=="generate":
        ids=[int(x) for x in args.training_ids.split(",") if x.strip()]
        generate_representations(args.task_file,ids,args.observation,args.output)
    else:
        compute(args.task_file,args.task_id,args.observation,args.representation,args.output_dir,args.ablate_window)

if __name__=="__main__":
    asyncio.run(main())
