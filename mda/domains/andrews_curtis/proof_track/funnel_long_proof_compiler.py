#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, bisect, importlib.util, json, re, sys
from collections import defaultdict
from pathlib import Path

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def parse_submission(path,cid):
    for line in Path(path).read_text().splitlines():
        m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
        if m and m.group(1)==cid:
            return list(ast.literal_eval(m.group(2)))
    raise KeyError(cid)

def replay_states(core,state,path):
    s=state;out=[s]
    for m in path:
        s=core.apply_move(s,m);out.append(s)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--submission",required=True)
    ap.add_argument("--projector-script",required=True)
    ap.add_argument("--challenge-id",default="ac-08551")
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    proj=load_module(Path(a.projector_script),"proj")
    acc=Path(a.acc_root);sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"];by={c["challenge_id"]:c for c in manifest["challenges"]}
    c=by[a.challenge_id]
    original=parse_submission(a.submission,a.challenge_id)
    v0=core.verify(c,original,c["move_spec_version"],limits)
    if not v0.get("ok"): raise RuntimeError(("original rejected",v0))

    initial=tuple(tuple(w) for w in c["initial_relators"])
    states=replay_states(core,initial,original)
    positions=defaultdict(list)
    for idx,s in enumerate(states): positions[s].append(idx)

    outgoing=defaultdict(list);rows=[]
    positive_defect=0;max_defect=0
    for t,s in enumerate(states[:-1]):
        for i in (0,1):
            end,best,_=proj.project_state(s,i)
            defect=sum(map(len,s))-sum(map(len,end))
            if defect>0:
                positive_defect+=1;max_defect=max(max_defect,defect)
            inds=positions.get(end,())
            k=bisect.bisect_right(inds,t)
            if k>=len(inds): continue
            u=inds[k]
            macro,chk,peak=proj.compile_projection(core,s,i,best["w"])
            if chk!=end: raise RuntimeError(("compiler mismatch",t,i))
            saving=(u-t)-len(macro)
            rec={
                "start":t,"end":u,"span":u-t,"i":i,
                "w":list(best["w"]),"macro_cost":len(macro),
                "saving":saving,"defect":defect,"peak":peak,
            }
            rows.append(rec)
            if saving>0: outgoing[t].append((u,tuple(macro),rec))

    n=len(original)
    dp=[0]*(n+1);choice=[None]*(n+1)
    dp[n]=0
    for t in range(n-1,-1,-1):
        best_cost=1+dp[t+1]
        best_choice=("orig",t+1,(original[t],),None)
        for u,macro,rec in outgoing.get(t,()):
            cost=len(macro)+dp[u]
            if cost<best_cost:
                best_cost=cost;best_choice=("macro",u,macro,rec)
        dp[t]=best_cost;choice[t]=best_choice

    optimized=[];used=[];t=0
    while t<n:
        kind,u,seg,rec=choice[t]
        optimized.extend(seg)
        if kind=="macro": used.append(rec)
        t=u

    v1=core.verify(c,optimized,c["move_spec_version"],limits)
    if not v1.get("ok"): raise RuntimeError(("optimized rejected",v1))

    report={
      "experiment":"ACC_FUNNEL_LONG_PROOF_COMPILER_V1",
      "challenge_id":a.challenge_id,
      "original_length":len(original),
      "optimized_length":len(optimized),
      "moves_saved":len(original)-len(optimized),
      "verified_original_hash":v0.get("certificate_hash"),
      "verified_optimized_hash":v1.get("certificate_hash"),
      "candidate_future_matches":len(rows),
      "profitable_candidate_edges":sum(r["saving"]>0 for r in rows),
      "selected_macro_edges":len(used),
      "positive_defect_observations":positive_defect,
      "max_defect":max_defect,
      "status":"VERIFIED_THEOREM_COMPILED_SHORTER_PROOF" if len(optimized)<len(original) else "NO_EXACT_TRAJECTORY_SHORTCUT",
      "claim_boundary":"Only exact future-state matches inside one already verifier-clean proof; no search or approximate state matching.",
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"candidate_edges.json").write_text(json.dumps(sorted(rows,key=lambda r:(-r["saving"],r["start"]))[:1000],indent=2,sort_keys=True)+"\n")
    (out/"selected_edges.json").write_text(json.dumps(used,indent=2,sort_keys=True)+"\n")
    (out/"optimized_submission.txt").write_text(f"{a.challenge_id}: {json.dumps(optimized,separators=(',',':'))}\n")
    print("FUNNEL_LONG_PROOF",json.dumps(report,sort_keys=True))
    for r in sorted(used,key=lambda r:r["start"]):
        print("FUNNEL_SHORTCUT",json.dumps(r,sort_keys=True))

if __name__=="__main__":main()
