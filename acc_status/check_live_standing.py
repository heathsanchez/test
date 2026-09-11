#!/usr/bin/env python3
import json, os, time
from pathlib import Path
from urllib import request, error

BASE="https://api.sair.foundation/api/public/v1"
KEY=os.environ["SAIR_API_KEY"]
OUT=Path(os.environ.get("ACC_STATUS_OUT","acc_status/out"))
OUT.mkdir(parents=True,exist_ok=True)

def api(path):
    req=request.Request(BASE+path,headers={
        "Authorization":f"Bearer {KEY}",
        "Accept":"application/json",
        "User-Agent":"curl/8.5.0",
    })
    try:
        with request.urlopen(req,timeout=60) as r:
            return r.status,json.loads(r.read().decode())
    except error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        raise RuntimeError(f"GET {path} HTTP {e.code}: {raw}")

def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

_,me=api("/competitions/acc/me")
save("me.json",me)
team=me["data"]["team"]
team_id=team["teamId"]
print("TEAM",team.get("teamNumber"),team_id,flush=True)

found={}
for attempt in range(1,16):
    found={}
    for problem in ("ac","stable_ac"):
        _,lb=api(f"/competitions/acc/leaderboard?problem={problem}")
        save(f"leaderboard_{problem}_{attempt:02d}.json",lb)
        items=lb.get("data",{}).get("items",[])
        hit=next((x for x in items if x.get("team",{}).get("teamId")==team_id),None)
        if hit:
            found[problem]={
                "generatedAt":lb.get("data",{}).get("generatedAt"),
                "rank":hit.get("rank"),
                "score":hit.get("score"),
                "currentBestCount":hit.get("currentBestCount"),
                "team":hit.get("team"),
            }
    print("ATTEMPT",attempt,json.dumps(found,sort_keys=True),flush=True)
    if len(found)==2:
        break
    time.sleep(20)

summary={
    "teamId":team_id,
    "teamNumber":team.get("teamNumber"),
    "teamName":team.get("teamName"),
    "published":found,
}
save("standing_summary.json",summary)
print("FINAL",json.dumps(summary,sort_keys=True),flush=True)
