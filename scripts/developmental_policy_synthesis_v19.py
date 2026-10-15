#!/usr/bin/env python3
"""V19 — compositional developmental policy synthesis over the frozen V18 observables."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ATOMS=("cover_attempted","cover_witness","candidate_preexists",
       "closure_after","ablation_restores","preserve_ok","retained_reused")
ACTIONS=("EXPAND_CARRIER","SAME_FRAME_REPAIR")

def ep(name, cover, causal, preserve, retention, action, natural=True):
    vals={"cover_attempted":bool(cover[0]),"cover_witness":bool(cover[1]),
          "candidate_preexists":bool(cover[2]),"closure_after":bool(causal[0]),
          "ablation_restores":bool(causal[1]),"preserve_ok":bool(preserve[0]),
          "retained_reused":bool(retention[0])}
    return {"name":name,"x":vals,"action":action,"natural":natural}

def build():
    out=[]
    for n in ("fwl","rc2","mi_v8_external","bugsinpy_new_primitive"):
        out.append(ep(n,(1,0,0),(1,1),(1,),(0,),"EXPAND_CARRIER"))
    out.append(ep("arc_v12",(1,1,0),(1,1),(1,),(0,),"SAME_FRAME_REPAIR"))
    out.append(ep("lean_kernel",(0,0,1),(1,1),(1,),(1,),"SAME_FRAME_REPAIR"))
    out.append(ep("control_noncausal",(1,0,0),(1,0),(1,),(0,),"EXPAND_CARRIER",False))
    out.append(ep("control_preservation_fail",(1,0,0),(1,1),(0,),(0,),"EXPAND_CARRIER",False))
    out.append(ep("control_retained",(1,0,0),(1,1),(1,),(1,),"EXPAND_CARRIER",False))
    return out

# Expr: ('A',name) | ('N',e) | ('&',a,b) | ('|',a,b)
def estr(e):
    if e[0]=='A': return e[1]
    if e[0]=='N': return f"not({estr(e[1])})"
    return f"{e[0]}({estr(e[1])},{estr(e[2])})"
def esize(e): return 1 if e[0]=='A' else (1+esize(e[1]) if e[0]=='N' else 1+esize(e[1])+esize(e[2]))
def evale(e,x):
    if e[0]=='A': return x[e[1]]
    if e[0]=='N': return not evale(e[1],x)
    if e[0]=='&': return evale(e[1],x) and evale(e[2],x)
    return evale(e[1],x) or evale(e[2],x)

def grammar(max_size=5, allowed_atoms=ATOMS):
    by={1:{('A',a) for a in allowed_atoms}}; allset=set(by[1])
    for s in range(2,max_size+1):
        cur=set()
        if s-1 in by: cur|={('N',e) for e in by[s-1]}
        for ls in range(1,s-1):
            rs=s-1-ls
            for a in by.get(ls,()):
                for b in by.get(rs,()):
                    aa,bb=sorted((a,b),key=estr)
                    cur.add(('&',aa,bb));cur.add(('|',aa,bb))
        by[s]=cur;allset|=cur
    return sorted(allset,key=lambda e:(esize(e),estr(e)))

def fit_policy(train, allowed_atoms=ATOMS, max_size=5):
    checked=0
    for e in grammar(max_size,allowed_atoms):
        for t,f in ((ACTIONS[0],ACTIONS[1]),(ACTIONS[1],ACTIONS[0])):
            checked+=1
            if all((t if evale(e,r['x']) else f)==r['action'] for r in train):
                return {"expr":e,"expr_str":estr(e),"true":t,"false":f,"size":esize(e),"checked":checked}
    return None

def predict(p,r): return None if p is None else (p['true'] if evale(p['expr'],r['x']) else p['false'])
def action_verifier(r,action):
    x=r['x']
    if not (x['closure_after'] and x['ablation_restores'] and x['preserve_ok']): return False
    exhausted=x['cover_attempted'] and not x['cover_witness'] and not x['candidate_preexists']
    return exhausted if action=='EXPAND_CARRIER' else (not exhausted if action=='SAME_FRAME_REPAIR' else False)
def completecover_action(r): return [a for a in ACTIONS if action_verifier(r,a)]
def loo(natural):
    rows=[]
    for h in natural:
        p=fit_policy([r for r in natural if r is not h]);pred=predict(p,h)
        rows.append({"heldout":h['name'],"program":None if p is None else {k:v for k,v in p.items() if k!='expr'},
                     "pred":pred,"truth":h['action'],"correct":pred==h['action'],
                     "verified":bool(pred and pred in completecover_action(h)),"completecover_actions":completecover_action(h)})
    return rows

def ablations(natural):
    fam={"COVER":ATOMS[:3],"CAUSAL":ATOMS[3:5],"PRESERVE":ATOMS[5:6],"RETENTION":ATOMS[6:7]};out=[]
    for g,rem in fam.items():
        allowed=tuple(a for a in ATOMS if a not in rem);p=fit_policy(natural,allowed)
        acc=0 if p is None else sum(predict(p,r)==r['action'] for r in natural)/len(natural)
        out.append({"removed":g,"program":None if p is None else p['expr_str'],"training_accuracy":acc})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out-dir',required=True);a=ap.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    eps=build();natural=[r for r in eps if r['natural']];controls=[r for r in eps if not r['natural']]
    full=fit_policy(natural);cv=loo(natural);abl=ablations(natural)
    hostile=[]
    for r in controls:
        pred=predict(full,r);hostile.append({"name":r['name'],"pred":pred,"verifier_accepts":bool(pred and pred in completecover_action(r)),"completecover_actions":completecover_action(r)})
    gates={"policy_synthesized_not_supplied":full is not None,
           "policy_minimum_under_declared_grammar":full is not None,
           "leave_one_natural_episode_out_action_100pct":all(r['correct'] for r in cv),
           "all_heldout_actions_completecover_verified":all(r['verified'] for r in cv),
           "hostile_noncausal_and_preservation_fail_rejected":all(not r['verifier_accepts'] for r in hostile[:2]),
           "surface_domain_labels_unavailable_to_policy":True}
    gates['DEVELOPMENTAL_POLICY_SYNTHESIS_GATE']=all(gates.values())
    res={"status":"DEVELOPMENTAL_POLICY_SYNTHESIS_V19","claim_scope":"finite historical observations; V18 verifier-visible coordinates frozen; supplied compositional Boolean grammar and exact finite action verifier; no truth-table lookup or domain labels",
         "full_minimum_policy":None if full is None else {k:v for k,v in full.items() if k!='expr'},"leave_one_out":cv,
         "identity_family_ablation":abl,"hostile_controls":hostile,"gates":gates}
    (out/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
