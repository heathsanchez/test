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

def replay_states(core,state,path):
    s=state; out=[s]
    for m in path:
        s=core.apply_move(s,m); out.append(s)
    return out

def loop_erase(path,states):
    n=len(path)
    future=defaultdict(list)
    for i,s in enumerate(states): future[s].append(i)
    next_same=[None]*(n+1)
    for inds in future.values():
        for a,b in zip(inds,inds[1:]): next_same[a]=b
    dp=[0]*(n+1); choice=[None]*(n+1)
    for i in range(n-1,-1,-1):
        best=1+dp[i+1]; ch=("orig",i+1)
        j=next_same[i]
        while j is not None:
            if dp[j] < best:
                best=dp[j]; ch=("jump",j)
            # later identical occurrences
            inds=future[states[i]]
            import bisect
            k=bisect.bisect_right(inds,j)
            j=inds[k] if k<len(inds) else None
        dp[i]=best; choice[i]=ch
    out=[]; jumps=[]; i=0
    while i<n:
        kind,j=choice[i]
        if kind=="orig": out.append(path[i])
        else: jumps.append({"start":i,"end":j,"saving":j-i})
        i=j
    return out,jumps

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--submission",required=True)
    ap.add_argument("--challenge-id",default="ac-08551")
    ap.add_argument("--funnel-report",required=True)
    ap.add_argument("--funnel-optimized",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    acc=Path(a.acc_root); sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; by={c["challenge_id"]:c for c in manifest["challenges"]}
    c=by[a.challenge_id]
    original=parse_submission(a.submission,a.challenge_id)
    v0=core.verify(c,original,c["move_spec_version"],limits)
    if not v0.get("ok"): raise RuntimeError(v0)
    init=tuple(tuple(w) for w in c["initial_relators"])
    states=replay_states(core,init,original)
    baseline,jumps=loop_erase(original,states)
    vb=core.verify(c,baseline,c["move_spec_version"],limits)
    if not vb.get("ok"): raise RuntimeError(vb)

    fr=json.loads(Path(a.funnel_report).read_text())
    fopt=parse_submission(a.funnel_optimized,a.challenge_id)
    vf=core.verify(c,fopt,c["move_spec_version"],limits)
    if not vf.get("ok"): raise RuntimeError(vf)

    report={
      "experiment":"ACC_FUNNEL_QUOTIENT_ABLATION_V1",
      "challenge_id":a.challenge_id,
      "original_length":len(original),
      "exact_loop_erased_length":len(baseline),
      "funnel_normalized_length":len(fopt),
      "exact_loop_saving":len(original)-len(baseline),
      "funnel_total_saving":len(original)-len(fopt),
      "incremental_funnel_gain":len(baseline)-len(fopt),
      "exact_loop_jumps":jumps,
      "funnel_selected_shortcuts":fr.get("selected_shortcuts"),
      "status":"CAUSAL_FUNNEL_COMPRESSION" if len(fopt)<len(baseline) else "NO_INCREMENTAL_FUNNEL_COMPRESSION",
      "claim_boundary":"Ablation compares exact-state loop erasure to funnel-normal-form quotient on the same frozen verifier-clean trajectory."
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"baseline_submission.txt").write_text(f"{a.challenge_id}: {json.dumps(baseline,separators=(',',':'))}\n")
    print("FUNNEL_ABLATION",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()
