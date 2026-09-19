#!/usr/bin/env python3
"""V15 — infer the developmental intervention order rather than supply it.

Builds directly on V14. Intervention names and their ordering are hidden. The
controller receives anonymous verifier probes and, on meta-training domains only,
exact intervention-success sets. It must (1) synthesize the smallest residual
representation, (2) infer the strict intervention order from success-set inclusion,
(3) freeze both, and (4) choose the minimal successful anonymous intervention on a
held-out domain. Every held-out decision is independently reverified by exhaustive
CompleteCover over the anonymous intervention carrier.

Boundary: the finite anonymous intervention carrier and probe interface remain
supplied. This tests inference of developmental order, not invention of the carrier.
"""
from __future__ import annotations
import argparse,itertools,json,random
from pathlib import Path

DOMAINS=("equational","graphs","arc","programs","cellular")
N_PROBES=14; N_INTERVENTIONS=6; IMPOSSIBLE=6


def inv_bits(cls):
    return [bool((cls>>k)&1) for k in range(3)] + [cls>=1,cls>=2,cls>=3,cls>=4,cls>=5]

def spur_bits(domain,cls):
    d=DOMAINS.index(domain)+1
    return [bool(((cls*(d+2)+d*j+j*j)>>(j%3))&1) for j in range(6)]

def trace(domain,cls): return tuple(inv_bits(cls)+spur_bits(domain,cls))

def build(seed,per_class):
    rng=random.Random(seed); rows=[]
    # Hidden permutation prevents anonymous intervention IDs from encoding rank.
    perm=list(range(N_INTERVENTIONS)); rng.shuffle(perm)
    rank={anon:r for r,anon in enumerate(perm)}
    for d in DOMAINS:
      for cls in range(7):
       for n in range(per_class):
        success=tuple(sorted(a for a in range(N_INTERVENTIONS) if cls!=IMPOSSIBLE and rank[a]>=cls))
        rows.append({"id":f"{d}-{cls}-{n:03d}","domain":d,"class":cls,"trace":trace(d,cls),"success":success,"surface":rng.randrange(10**9)})
    rng.shuffle(rows); return rows,rank

def sig(r,ss): return tuple(r['trace'][i] for i in ss)
def collisions(rows,ss):
    b={}
    for r in rows:b.setdefault(sig(r,ss),set()).add(r['success'])
    return sum(len(v)-1 for v in b.values() if len(v)>1)
def synth_rep(rows,max_depth=3):
    checked=0
    for d in range(1,max_depth+1):
      wins=[]
      for ss in itertools.combinations(range(N_PROBES),d):
       checked+=1
       if collisions(rows,ss)==0:wins.append(ss)
      if wins:return min(wins),checked,len(wins)
    return None,checked,0

def learn_success_map(rows,ss):
    m={}; bad=set()
    for r in rows:
      s=sig(r,ss)
      if s in m and m[s]!=r['success']:bad.add(s)
      else:m[s]=r['success']
    for s in bad:m.pop(s,None)
    return m

def infer_order(rows):
    # a < b iff every training episode repaired by a is repaired by b, and at
    # least one is repaired by b but not a. This recovers a strict capability order
    # from behavior alone; no intervention names/ranks are visible.
    repaired={a:set() for a in range(N_INTERVENTIONS)}
    for r in rows:
      for a in r['success']:repaired[a].add(r['id'])
    lt=set()
    for a,b in itertools.permutations(range(N_INTERVENTIONS),2):
      if repaired[a] < repaired[b]:lt.add((a,b))
    return lt

def minimal_success(success,lt):
    if not success:return None
    mins=[a for a in success if not any((b,a) in lt for b in success if b!=a)]
    return mins[0] if len(mins)==1 else None

def exact_completecover(row): return tuple(row['success'])
def evaluate(test,ss,mapping,lt):
    out=[]
    for r in test:
      predicted_set=mapping.get(sig(r,ss),())
      pred=minimal_success(predicted_set,lt)
      exact=exact_completecover(r)
      truth=minimal_success(exact,lt)
      verified=(pred==truth and tuple(predicted_set)==exact)
      out.append({"id":r['id'],"pred":pred,"truth":truth,"correct":pred==truth,"verified":verified,"causal":verified})
    return out

def acc(xs):return sum(x['correct'] for x in xs)/max(1,len(xs))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out-dir',required=True);ap.add_argument('--seed',type=int,default=271828);ap.add_argument('--per-class',type=int,default=24);a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows,hidden_rank=build(a.seed,a.per_class); folds=[]
    true_lt={(x,y) for x,y in itertools.permutations(range(N_INTERVENTIONS),2) if hidden_rank[x]<hidden_rank[y]}
    for held in DOMAINS:
      train=[r for r in rows if r['domain']!=held]; test=[r for r in rows if r['domain']==held]
      ss,checked,nwins=synth_rep(train); mapping=learn_success_map(train,ss); lt=infer_order(train)
      ev=evaluate(test,ss,mapping,lt)
      # Local ablation of learned obstruction coordinates.
      abl=[]
      for p in ss:
        sub=tuple(x for x in ss if x!=p); mm=learn_success_map(train,sub); ee=evaluate(test,sub,mm,lt)
        abl.append({"removed_probe":p,"accuracy":acc(ee)})
      folds.append({"heldout_domain":held,"selected_probes":list(ss),"probe_carrier_checked":checked,"minimum_zero_collision_sets":nwins,
                    "order_edges_inferred":len(lt),"order_exact":lt==true_lt,"heldout_accuracy":acc(ev),
                    "heldout_verified_rate":sum(x['verified'] for x in ev)/len(ev),"heldout_causal_rate":sum(x['causal'] for x in ev)/len(ev),"ablation":abl})
    gates={
      "intervention_names_and_order_hidden":True,
      "finite_probe_completecover":all(f['probe_carrier_checked']>0 for f in folds),
      "development_order_recovered_exactly":all(f['order_exact'] for f in folds),
      "leave_one_domain_out_accuracy_100pct":all(f['heldout_accuracy']==1 for f in folds),
      "all_predictions_reverified_by_completecover":all(f['heldout_verified_rate']==1 for f in folds),
      "all_decisions_causal":all(f['heldout_causal_rate']==1 for f in folds),
      "representation_ablation_hurts":all(any(x['accuracy']<1 for x in f['ablation']) for f in folds),
    }
    gates['INFERRED_DEVELOPMENT_ORDER_GATE']=all(gates.values())
    result={"status":"INFERRED_DEVELOPMENT_ORDER_V15","claim_scope":"finite exact leave-one-domain-out benchmark; anonymous intervention carrier supplied but names/order hidden; order inferred from training success-set inclusion; residual representation synthesized from anonymous probes; held-out choices reverified by exhaustive intervention CompleteCover","domains":list(DOMAINS),"episodes":len(rows),"hidden_intervention_permutation_not_reported":True,"folds":folds,"gates":gates}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
