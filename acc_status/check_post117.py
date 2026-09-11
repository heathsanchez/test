#!/usr/bin/env python3
import json,os,time
from pathlib import Path
from urllib import request

BASE="https://api.sair.foundation/api/public/v1"
KEY=os.environ["SAIR_API_KEY"]
OUT=Path("acc_status/post117"); OUT.mkdir(parents=True,exist_ok=True)
MIN=int(os.environ.get("MIN_SCORING","20"))

def get(path):
    req=request.Request(BASE+path,headers={"Authorization":f"Bearer {KEY}","Accept":"application/json","User-Agent":"curl/8.5.0"})
    with request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())

me=get("/competitions/acc/me")
team=me["data"]["team"]; tid=team["teamId"]
best={}
for attempt in range(1,16):
    cur={}
    for problem in ("ac","stable_ac"):
        lb=get(f"/competitions/acc/leaderboard?problem={problem}")
        (OUT/f"{problem}_{attempt:02d}.json").write_text(json.dumps(lb,indent=2,sort_keys=True)+"\n")
        hit=next((x for x in lb.get("data",{}).get("items",[]) if x.get("team",{}).get("teamId")==tid),None)
        if hit:
            cur[problem]={
                "generatedAt":lb.get("data",{}).get("generatedAt"),
                "rank":hit.get("rank"),"score":hit.get("score"),
                "currentBestCount":hit.get("currentBestCount")
            }
    best=cur
    print("ATTEMPT",attempt,json.dumps(cur,sort_keys=True),flush=True)
    if len(cur)==2 and min(int(x.get("currentBestCount") or 0) for x in cur.values())>=MIN: break
    time.sleep(20)
summary={"team":team,"standing":best,"min_scoring_gate":MIN}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print("FINAL",json.dumps(summary,sort_keys=True))
