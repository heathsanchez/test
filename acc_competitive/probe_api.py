#!/usr/bin/env python3
import json, os
from pathlib import Path
from urllib import request, error

BASE="https://api.sair.foundation/api/public/v1"
KEY=os.environ["SAIR_API_KEY"]
OUT=Path("acc_competitive/probe_out"); OUT.mkdir(parents=True,exist_ok=True)
paths=[
  "/competitions/acc/challenges/ac-00001",
  "/competitions/acc/challenges/ac-00001/leaderboard",
  "/competitions/acc/challenges/ac-00001/teams",
  "/competitions/acc/records/ac-00001",
  "/competitions/acc/records?problem=ac&challengeId=ac-00001",
  "/competitions/acc/solutions?challengeId=ac-00001",
  "/competitions/acc/challenges?problem=ac&challengeId=ac-00001",
]
summary=[]
for i,path in enumerate(paths):
    req=request.Request(BASE+path,headers={
      "Authorization":f"Bearer {KEY}",
      "Accept":"application/json",
      "User-Agent":"curl/8.5.0",
    })
    status=None; body=None
    try:
        with request.urlopen(req,timeout=30) as r:
            status=r.status
            raw=r.read().decode(errors="replace")
    except error.HTTPError as e:
        status=e.code
        raw=e.read().decode(errors="replace")
    try: body=json.loads(raw)
    except Exception: body={"raw":raw[:2000]}
    (OUT/f"{i:02d}.json").write_text(json.dumps({"path":path,"status":status,"body":body},indent=2,sort_keys=True)+"\n")
    keys=[]
    if isinstance(body,dict):
        keys=list(body.keys())
        data=body.get("data")
        if isinstance(data,dict): keys+=["data."+k for k in data.keys()]
    summary.append({"path":path,"status":status,"keys":keys})
print("PROBE",json.dumps(summary,sort_keys=True))
(OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
