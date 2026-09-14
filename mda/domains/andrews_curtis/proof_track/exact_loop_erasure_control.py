#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, re, sys
from collections import defaultdict
from pathlib import Path

def parse_submission(path,cid):
    for line in Path(path).read_text().splitlines():
        m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
        if m and m.group(1)==cid:
            return list(ast.literal_eval(m.group(2)))
    raise KeyError(cid)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--submission",required=True)
    ap.add_argument("--challenge-id",default="ac-08551")
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    acc=Path(a.acc_root);sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"];by={c["challenge_id"]:c for c in manifest["challenges"]}
    c=by[a.challenge_id]
    path=parse_submission(a.submission,a.challenge_id)
    v0=core.verify(c,path,c["move_spec_version"],limits)
    if not v0.get("ok"): raise RuntimeError(v0)

    s=tuple(tuple(w) for w in c["initial_relators"])
    states=[s]
    for m in path:
        s=core.apply_move(s,m);states.append(s)

    pos=defaultdict(list)
    for i,s in enumerate(states):pos[s].append(i)

    by_start=defaultdict(list)
    for inds in pos.values():
        for ai,aidx in enumerate(inds[:-1]):
            for bidx in inds[ai+1:]:
                by_start[aidx].append(bidx)

    n=len(path);dp=[0]*(n+1);choice=[None]*(n+1)
    for t in range(n-1,-1,-1):
        best=1+dp[t+1];ch=("orig",t+1)
        for u in by_start.get(t,()):
            if dp[u]<best:
                best=dp[u];ch=("jump",u)
        dp[t]=best;choice[t]=ch

    opt=[];jumps=[];t=0
    while t<n:
        kind,u=choice[t]
        if kind=="orig":opt.append(path[t])
        else:jumps.append({"start":t,"end":u,"saving":u-t})
        t=u
    v1=core.verify(c,opt,c["move_spec_version"],limits)
    if not v1.get("ok"): raise RuntimeError(v1)

    report={
      "experiment":"ACC_EXACT_STATE_LOOP_ERASURE_CONTROL_V1",
      "challenge_id":a.challenge_id,
      "original_length":len(path),"optimized_length":len(opt),
      "moves_saved":len(path)-len(opt),"selected_jumps":len(jumps),
      "verified_original_hash":v0.get("certificate_hash"),
      "verified_optimized_hash":v1.get("certificate_hash"),
      "status":"VERIFIED_EXACT_LOOP_ERASURE",
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"jumps.json").write_text(json.dumps(jumps,indent=2,sort_keys=True)+"\n")
    print("EXACT_LOOP_ERASURE",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()
