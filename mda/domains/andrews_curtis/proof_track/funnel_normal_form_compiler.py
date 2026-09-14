#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, importlib.util, json, re, sys
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

def total(s): return sum(map(len,s))

def reverse_path(core,path):
    return tuple(core.INVERSE_MOVE[m] for m in reversed(tuple(path)))

def normalize(core,proj,state,limit):
    s=state; path=[]; steps=[]
    seen={s}
    while True:
        arms=[]
        for i in (0,1):
            end,best,_ties=proj.project_state(s,i)
            gain=total(s)-total(end)
            if gain<=0:
                continue
            macro,chk,peak=proj.compile_projection(core,s,i,best["w"])
            if chk!=end:
                raise RuntimeError(("compiler mismatch",s,i))
            if peak>limit:
                continue
            arms.append(( -gain, len(macro), i, tuple(best["w"]), end, tuple(macro), peak ))
        if not arms:
            break
        arms.sort()
        ng,mc,i,w,end,macro,peak=arms[0]
        if end in seen:
            raise RuntimeError("strict descent cycle")
        steps.append({
            "i":i,"w":list(w),"gain":-ng,"atomic_cost":mc,
            "before_total":total(s),"after_total":total(end),"peak":peak,
        })
        path.extend(macro); s=end; seen.add(s)
    chk=state
    for m in path: chk=core.apply_move(chk,m)
    if chk!=s: raise RuntimeError("normalization replay mismatch")
    return s,tuple(path),steps

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

    memo={}
    norms=[]
    for idx,s in enumerate(states):
        if s not in memo:
            memo[s]=normalize(core,proj,s,limits["max_total_relator_length"])
        nf,p,steps=memo[s]
        norms.append((nf,p,steps))
        if idx%250==0:
            print("NORMALIZE_PROGRESS",json.dumps({
                "index":idx,"state_total":total(s),"nf_total":total(nf),
                "norm_cost":len(p),"norm_steps":len(steps)
            },sort_keys=True),flush=True)

    groups=defaultdict(list)
    for idx,(nf,p,steps) in enumerate(norms):
        groups[nf].append(idx)

    edges=[]
    for nf,inds in groups.items():
        if len(inds)<2: continue
        # all earlier->later pairs in the same deterministic quotient class
        # are exact paths via the shared normal form.
        for ai,aidx in enumerate(inds[:-1]):
            pa=norms[aidx][1]
            for bidx in inds[ai+1:]:
                pb=norms[bidx][1]
                macro=pa+reverse_path(core,pb)
                span=bidx-aidx
                saving=span-len(macro)
                if saving<=0: continue
                edges.append({
                    "start":aidx,"end":bidx,"span":span,
                    "shortcut_cost":len(macro),"saving":saving,
                    "nf_total":total(nf),
                    "start_norm_cost":len(pa),"end_norm_cost":len(pb),
                    "macro":list(macro),
                })

    by_start=defaultdict(list)
    for e in edges: by_start[e["start"]].append(e)

    n=len(original)
    dp=[0]*(n+1);choice=[None]*(n+1)
    for t in range(n-1,-1,-1):
        best=1+dp[t+1]; ch=("orig",t+1,(original[t],),None)
        for e in by_start.get(t,()):
            cost=e["shortcut_cost"]+dp[e["end"]]
            if cost<best:
                best=cost;ch=("nf",e["end"],tuple(e["macro"]),e)
        dp[t]=best;choice[t]=ch

    opt=[];selected=[];t=0
    while t<n:
        kind,u,seg,e=choice[t]
        opt.extend(seg)
        if kind=="nf": selected.append({k:v for k,v in e.items() if k!="macro"})
        t=u

    v1=core.verify(c,opt,c["move_spec_version"],limits)
    if not v1.get("ok"): raise RuntimeError(("optimized rejected",v1))

    class_sizes=sorted((len(v) for v in groups.values()),reverse=True)
    report={
        "experiment":"ACC_FUNNEL_NORMAL_FORM_COMPILER_V1",
        "challenge_id":a.challenge_id,
        "trajectory_states":len(states),
        "unique_exact_states":len(set(states)),
        "unique_funnel_normal_forms":len(groups),
        "nontrivial_normalizations":sum(bool(p) for _,p,_ in norms),
        "max_normalization_length_drop":max(total(states[i])-total(norms[i][0]) for i in range(len(states))),
        "largest_normal_form_class":class_sizes[0] if class_sizes else 0,
        "shortcut_candidates":len(edges),
        "selected_shortcuts":len(selected),
        "original_length":len(original),
        "optimized_length":len(opt),
        "moves_saved":len(original)-len(opt),
        "verified_original_hash":v0.get("certificate_hash"),
        "verified_optimized_hash":v1.get("certificate_hash"),
        "status":"VERIFIED_FUNNEL_QUOTIENT_COMPRESSION" if len(opt)<len(original) else "NO_FUNNEL_QUOTIENT_COMPRESSION",
        "claim_boundary":"Deterministic strict-descent quotient using only exact nearest-conjugate funnel projections admitted by the official verifier limits."
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"selected_shortcuts.json").write_text(json.dumps(selected,indent=2,sort_keys=True)+"\n")
    (out/"best_shortcuts.json").write_text(json.dumps(sorted([{k:v for k,v in e.items() if k!="macro"} for e in edges],key=lambda e:(-e["saving"],e["start"]))[:500],indent=2,sort_keys=True)+"\n")
    (out/"optimized_submission.txt").write_text(f"{a.challenge_id}: {json.dumps(opt,separators=(',',':'))}\n")
    print("FUNNEL_NORMAL_FORM",json.dumps(report,sort_keys=True))
    for e in selected:
        print("FUNNEL_NORMAL_SHORTCUT",json.dumps(e,sort_keys=True))

if __name__=="__main__": main()
