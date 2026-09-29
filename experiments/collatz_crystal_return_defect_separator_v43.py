#!/usr/bin/env python3
"""Crystal V43: minimum return-defect separator after V42 same-source collision.

V42 proves source identity is insufficient: one exact natural source revisits
one V40 intrinsic cell under the same exact return law and then takes different
next consequences.  Therefore refine only the return-coordinate information.

State under test:
  (V40 intrinsic cell, exact current same-anchor return law,
   m mod 2^a, m mod 3^b)
where x=2^r*m-1 is the current episode anchor coordinate.

Fit the minimum global (a,b) on TRAIN motifs ZERO/ONES/110, freeze it, then
prospectively test HOLDOUT motifs 101/011/ALT01.  New episode anchors outside
V40 remain a separate grammar residual and are reported, not hidden.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from contextlib import redirect_stdout
import hashlib,io,json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

BASE_DEPTH=9
SUFFIX_BITS=18
CAP=700
MOD3=3**4
TRAIN=("ZERO","ONES","110")
HOLDOUT=("101","011","ALT01")
ALL=TRAIN+HOLDOUT
MAX_A=64
MAX_B=20

def live_frontier(depth):
    frontier=[0]
    for d in range(depth+1):
        survivors=[];nxt=[]
        for r in frontier:
            z=v25.classify_cell(d,r,with_merge=True)
            if not z["terminal"]:
                survivors.append(r)
                if d<depth:nxt.extend((r,r+(1<<d)))
        if d==depth:return survivors
        frontier=nxt
LIVE=live_frontier(BASE_DEPTH)
assert len(LIVE)==64

def motif_bits(name):
    if name=="ZERO":return 0
    if name=="ONES":return (1<<SUFFIX_BITS)-1
    if name in ("110","101","011"):
        p=[int(c) for c in name]
        return sum(p[i%3]<<i for i in range(SUFFIX_BITS))
    if name=="ALT01":return sum((i&1)<<i for i in range(SUFFIX_BITS))
    raise KeyError(name)

M2=1<<(BASE_DEPTH+SUFFIX_BITS)
INV2=pow(M2,-1,MOD3)
def crt_parameter(r,a3,motif):
    t2=r+(motif_bits(motif)<<BASE_DEPTH)
    t=t2+M2*(((a3-t2)*INV2)%MOD3)
    assert t%M2==t2 and t%MOD3==a3
    return t

def law_key(e):
    c=e["cert"]
    return (e["anchor"],c["A"],c["B"],c["D"],c["rho"])

def phase_state(e,a,b):
    ik,_=v40.event_keys(e)
    m=e["m0"]
    return (
      ik, law_key(e),
      m%(1<<a) if a else 0,
      m%(3**b) if b else 0,
    )

# Collect exact return-event rows once.
raw=[]
stats=Counter()
first_new_anchor=None
for r in LIVE:
  for a3 in range(MOD3):
    for motif in ALL:
      t=crt_parameter(r,a3,motif)
      n=v25.N0+v25.NC*t
      rr=v40.actual_episode_returns(f"r{r}-a{a3}-{motif}",n,CAP)
      if rr["note"]=="ordinary exit before zero-tail":
          stats["EXIT_PRE_ZERO"]+=1; continue
      stats["POST_ZERO"]+=1
      by=defaultdict(list)
      for e in rr["events"]:
          if e["anchor"] not in v40.banks:
              stats["NEW_ANCHOR_EVENTS"]+=1
              if first_new_anchor is None:
                  first_new_anchor={"r":r,"a3":a3,"motif":motif,"t":str(t),
                    "source":str(n),"anchor":e["anchor"],"k0":e["k0"],"k1":e["k1"]}
              continue
          e["ik"],_=v40.event_keys(e)
          e["law"]=law_key(e)
          by[e["anchor"]].append(e)
      for anchor,es in by.items():
          es.sort(key=lambda z:(z["k0"],z["k1"]))
          for i,e in enumerate(es):
              if i+1<len(es):
                  y=es[i+1]
                  cons=("NEXT",y["ik"],y["law"])
              else:
                  cons=("EXIT",rr["first_exit"]["kind"] if rr["first_exit"] else "CAP")
              raw.append({"motif":motif,"t":t,"source":n,"r":r,"a3":a3,
                 "e":e,"cons":cons})

train=[z for z in raw if z["motif"] in TRAIN]
hold=[z for z in raw if z["motif"] in HOLDOUT]
stats["ROWS"]=len(raw);stats["TRAIN_ROWS"]=len(train);stats["HOLDOUT_ROWS"]=len(hold)

def key(z,a,b): return phase_state(z["e"],a,b)

def grouped(data,a,b):
    g=defaultdict(set);w=defaultdict(list)
    for z in data:
        k=key(z,a,b)
        g[k].add(repr(z["cons"]))
        w[k].append(z)
    return g,w

def bad_groups(data,a,b):
    g,w=grouped(data,a,b)
    return {k:v for k,v in g.items() if len(v)>1},w

candidates=[]
for a in range(MAX_A+1):
  for b in range(MAX_B+1):
    bad,_=bad_groups(train,a,b)
    if not bad:candidates.append((a+b,a,b))

def pack(z,a,b):
    e=z["e"]; c=e["cert"]
    return {
      "motif":z["motif"],"t":str(z["t"]),"source":str(z["source"]),
      "source_cell_r":z["r"],"source_a3":z["a3"],
      "anchor":e["anchor"],"depth":[e["k0"],e["k1"]],
      "m0":str(e["m0"]),"m1":str(e["m1"]),
      "law":repr(e["law"]),"intrinsic":repr(e["ik"]),
      "defect":str(e["defect"]),
      "m_mod_2a":e["m0"]%(1<<a) if a else 0,
      "m_mod_3b":e["m0"]%(3**b) if b else 0,
      "consequence":repr(z["cons"]),
    }

if not candidates:
    bad,w=bad_groups(train,MAX_A,MAX_B)
    k=next(iter(bad))
    result={
      "schema":"COLLATZ_CRYSTAL_RETURN_DEFECT_SEPARATOR_V43",
      "parent":"collatz-crystal-normalized-source-separator-v42@e5ec94a85d0790edbdc5d2d4a683ffac5c0b3e34",
      "stats":dict(sorted(stats.items())),
      "max_precision_failure":{"a":MAX_A,"b":MAX_B,"collision_keys":len(bad),
        "first_key":repr(k),"rows":[pack(z,MAX_A,MAX_B) for z in w[k][:12]]},
      "first_new_anchor_event":first_new_anchor,
      "verdict":"RETURN_RESIDUE_SEPARATOR_NOT_FOUND_WITHIN_DECLARED_PRECISION",
      "global_collatz":"UNKNOWN",
    }
    result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0)

_,A,B=min(candidates)
train_g,train_w=grouped(train,A,B)
assert all(len(v)==1 for v in train_g.values())
train_cons={k:next(iter(v)) for k,v in train_g.items()}

hold_g,hold_w=grouped(hold,A,B)
hold_internal={k:v for k,v in hold_g.items() if len(v)>1}
cross={k:(train_cons[k],sorted(v)) for k,v in hold_g.items()
       if k in train_cons and (len(v)!=1 or next(iter(v))!=train_cons[k])}

first_failure=None
if hold_internal:
    k=next(iter(hold_internal))
    first_failure={"kind":"HOLDOUT_INTERNAL_COLLISION","key":repr(k),
      "rows":[pack(z,A,B) for z in hold_w[k][:12]]}
elif cross:
    k=next(iter(cross))
    rows=[z for z in train+hold if key(z,A,B)==k]
    first_failure={"kind":"TRAIN_HOLDOUT_MISMATCH","key":repr(k),
      "rows":[pack(z,A,B) for z in rows[:12]]}

# Per-state minima expose whether one global width is overkill.
per_base={}
bases=sorted({(z["e"]["ik"],z["e"]["law"]) for z in train},key=repr)
for base in bases:
    ds=[z for z in train if (z["e"]["ik"],z["e"]["law"])==base]
    best=None
    for a in range(MAX_A+1):
      for b in range(MAX_B+1):
        bad,_=bad_groups(ds,a,b)
        if not bad:
            cand=(a+b,a,b)
            if best is None or cand<best:best=cand
    if best:
        per_base[repr(base)]={"a":best[1],"b":best[2],"rows":len(ds)}
    else:
        per_base[repr(base)]={"a":None,"b":None,"rows":len(ds)}

verdict=("RETURN_DEFECT_SEPARATOR_HOLDOUT_REJECTED"
         if hold_internal or cross else
         "RETURN_DEFECT_SEPARATOR_SURVIVES_HELD_OUT_MOTIFS")

result={
 "schema":"COLLATZ_CRYSTAL_RETURN_DEFECT_SEPARATOR_V43",
 "parent":"collatz-crystal-normalized-source-separator-v42@e5ec94a85d0790edbdc5d2d4a683ffac5c0b3e34",
 "corpus":{"v25_live_cells":len(LIVE),"ternary_classes":MOD3,
   "suffix_bits":SUFFIX_BITS,"train_motifs":list(TRAIN),"holdout_motifs":list(HOLDOUT)},
 "stats":dict(sorted(stats.items())),
 "frozen_separator":{
   "a_owner_binary_bits":A,"b_owner_ternary_trits":B,
   "mod2":str(1<<A),"mod3":str(3**B),"train_functional":True},
 "per_phase_state_train_minima":per_base,
 "holdout":{"internal_collision_keys":len(hold_internal),
   "train_holdout_mismatch_keys":len(cross),"first_failure":first_failure},
 "first_new_anchor_event":first_new_anchor,
 "verdict":verdict,
 "interpretation":(
   "V42's same-source collision is resolved, when possible, by refining only "
   "the episode-owner/return-defect coordinate while preserving exact return "
   "law identity. This is the separator-driven A8 Q3/Q2 refinement, not a "
   "deeper raw-source census."
 ),
 "promotion_boundary":(
   "A green holdout remains bounded. Universal QED still requires an all-depth "
   "reselection/completeness theorem and inclusion/elimination of new anchors."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
