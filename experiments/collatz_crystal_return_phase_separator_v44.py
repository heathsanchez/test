#!/usr/bin/env python3
"""V44: minimum return-phase separator after the V42 same-source collision.

V42 proved that even exact V23 source parameter identity plus the V40
intrinsic Q2xQ3 return cell is not future-functional: one fixed natural source
can revisit one intrinsic cell with different protected next consequences.

This gate keeps the source and intrinsic cell fixed and asks which omitted
CURRENT-RETURN coordinate is actually consequential.  Since the intrinsic
cell already carries (anchor,D+1,rho,Q3-cell), the exact affine law
    m' = (A*m+B)/2^D,  A=3^q
has only q (equivalently A) and B left as law data.  We test q, B, their pair,
and small defect-valuation augmentations on TRAIN motifs, freeze the smallest
successful representation, and prospectively challenge it on HOLDOUT motifs.

Bounded separator discovery only; no global Collatz claim.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from contextlib import redirect_stdout
import hashlib, io, json

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

def v2z(x:int):
    x=abs(x)
    if x==0: return None
    return (x & -x).bit_length()-1

def v3z(x:int):
    x=abs(x)
    if x==0: return None
    v=0
    while x%3==0:
        x//=3; v+=1
    return v

def pow3_exp(x:int):
    q=0
    while x>1 and x%3==0:
        x//=3; q+=1
    assert x==1
    return q

def live_frontier(depth:int):
    frontier=[0]
    for d in range(depth+1):
        survivors=[]; nxt=[]
        for r in frontier:
            z=v25.classify_cell(d,r,with_merge=True)
            if not z["terminal"]:
                survivors.append(r)
                if d<depth:
                    nxt.extend((r,r+(1<<d)))
        if d==depth:
            return survivors
        frontier=nxt
    raise AssertionError

LIVE=live_frontier(BASE_DEPTH)
assert len(LIVE)==64

def motif_bits(name:str):
    if name=="ZERO": return 0
    if name=="ONES": return (1<<SUFFIX_BITS)-1
    if name in ("110","101","011"):
        p=[int(c) for c in name]
        return sum(p[i%3]<<i for i in range(SUFFIX_BITS))
    if name=="ALT01":
        return sum((i&1)<<i for i in range(SUFFIX_BITS))
    raise KeyError(name)

M2=1<<(BASE_DEPTH+SUFFIX_BITS)
INV2=pow(M2,-1,MOD3)

def crt_parameter(r:int,a3:int,motif:str):
    t2=r+(motif_bits(motif)<<BASE_DEPTH)
    k=((a3-t2)*INV2)%MOD3
    t=t2+M2*k
    assert t%M2==t2 and t%MOD3==a3
    return t

def intrinsic(e):
    if e["anchor"] not in v40.banks:
        return None
    ik,_=v40.event_keys(e)
    return ik

rows=[]
stats=Counter()
for r in LIVE:
    for a3 in range(MOD3):
        for motif in ALL:
            t=crt_parameter(r,a3,motif)
            n=v25.N0+v25.NC*t
            rr=v40.actual_episode_returns(f"r{r}-a{a3}-{motif}",n,CAP)
            if rr["note"]=="ordinary exit before zero-tail":
                stats["EXIT_PRE_ZERO"]+=1
                continue
            stats["POST_ZERO"]+=1
            by=defaultdict(list)
            for e in rr["events"]:
                if e["anchor"] not in v40.banks:
                    stats["NEW_ANCHOR_EVENTS"]+=1
                    continue
                e["ik"]=intrinsic(e)
                by[e["anchor"]].append(e)
            for anchor,es in by.items():
                es.sort(key=lambda z:(z["k0"],z["k1"]))
                for i,e in enumerate(es):
                    cons=("EXIT", rr["first_exit"]["kind"] if rr["first_exit"] else "CAP") if i+1==len(es) else ("NEXT",es[i+1]["ik"])
                    c=e["cert"]
                    q=pow3_exp(c["A"])
                    defect=e["defect"]
                    rows.append({
                      "motif":motif,"t":t,"source":n,
                      "state":e["ik"],"cons":cons,
                      "anchor":anchor,"k0":e["k0"],"k1":e["k1"],
                      "q":q,"A":c["A"],"B":c["B"],"D":c["D"],"rho":c["rho"],
                      "cert_id":e["cert_id"],
                      "defect":defect,"dv2":v2z(defect),"dv3":v3z(defect),
                      "m0":e["m0"],"m1":e["m1"],
                    })

stats["ROWS"]=len(rows)
train=[z for z in rows if z["motif"] in TRAIN]
hold=[z for z in rows if z["motif"] in HOLDOUT]
stats["TRAIN_ROWS"]=len(train); stats["HOLDOUT_ROWS"]=len(hold)

FEATURES=[
 ("NONE", lambda z: ()),
 ("ODD_COUNT_Q", lambda z: (z["q"],)),
 ("COCYCLE_B", lambda z: (z["B"],)),
 ("DEFECT_V3", lambda z: (z["dv3"],)),
 ("DEFECT_V2V3", lambda z: (z["dv2"],z["dv3"])),
 ("Q_DEFECT_V3", lambda z: (z["q"],z["dv3"])),
 ("B_DEFECT_V3", lambda z: (z["B"],z["dv3"])),
 ("EXACT_LAW_QB", lambda z: (z["q"],z["B"])),
 ("LAW_PLUS_DEFECT_V2V3", lambda z: (z["q"],z["B"],z["dv2"],z["dv3"])),
]

def key(z,fn):
    # Exact source identity is intentional: V42 already proved source precision
    # itself is not the missing coordinate.  We now isolate phase information.
    return (z["state"],z["t"],fn(z))

def conflicts(data,fn):
    g=defaultdict(set); wr=defaultdict(list)
    for z in data:
        k=key(z,fn)
        g[k].add(repr(z["cons"]))
        wr[k].append(z)
    return {k:v for k,v in g.items() if len(v)>1},wr

def pack(z):
    return {
      "motif":z["motif"],"t":str(z["t"]),"source":str(z["source"]),
      "state":repr(z["state"]),"depth":[z["k0"],z["k1"]],
      "q":z["q"],"A":str(z["A"]),"B":str(z["B"]),
      "D":z["D"],"rho":str(z["rho"]),"cert_id":z["cert_id"],
      "defect":str(z["defect"]),"defect_v2":z["dv2"],"defect_v3":z["dv3"],
      "m0":str(z["m0"]),"m1":str(z["m1"]),
      "consequence":repr(z["cons"]),
    }

train_audit={}
chosen=None
chosen_fn=None
for name,fn in FEATURES:
    bad,wr=conflicts(train,fn)
    train_audit[name]={"collision_keys":len(bad)}
    if bad:
        k=sorted(bad,key=repr)[0]
        train_audit[name]["first_collision"]={
          "key":repr(k),"consequences":sorted(bad[k]),
          "rows":[pack(z) for z in wr[k][:6]],
        }
    if chosen is None and not bad:
        chosen=name; chosen_fn=fn

if chosen is None:
    verdict="TESTED_PHASE_FEATURES_INSUFFICIENT"
    hold_summary=None
else:
    # Prospective holdout: require internal functionality, and exact agreement
    # whenever the same protected key was already observed in TRAIN.
    train_map={}
    for z in train:
        train_map[key(z,chosen_fn)]=repr(z["cons"])
    hbad,hwr=conflicts(hold,chosen_fn)
    cross={}
    for z in hold:
        k=key(z,chosen_fn); c=repr(z["cons"])
        if k in train_map and train_map[k]!=c:
            cross.setdefault(k,set()).update((train_map[k],c))
    first=None
    if hbad:
        k=sorted(hbad,key=repr)[0]
        first={"kind":"HOLDOUT_INTERNAL_COLLISION","key":repr(k),
               "consequences":sorted(hbad[k]),
               "rows":[pack(z) for z in hwr[k][:6]]}
    elif cross:
        k=sorted(cross,key=repr)[0]
        rs=[z for z in train+hold if key(z,chosen_fn)==k]
        first={"kind":"TRAIN_HOLDOUT_MISMATCH","key":repr(k),
               "consequences":sorted(cross[k]),
               "rows":[pack(z) for z in rs[:8]]}
    hold_summary={
      "internal_collision_keys":len(hbad),
      "train_holdout_mismatch_keys":len(cross),
      "first_failure":first,
    }
    verdict=("RETURN_PHASE_SEPARATOR_HOLDOUT_REJECTED"
             if hbad or cross else
             "RETURN_PHASE_SEPARATOR_SURVIVES_HELD_OUT_MOTIFS")

result={
 "schema":"COLLATZ_CRYSTAL_RETURN_PHASE_SEPARATOR_V44",
 "parents":{
   "v41":"collatz-crystal-v40-bank-challenge-v41@2283822c221f17cce47c954c203036c5138a0ae2",
   "v42":"collatz-crystal-normalized-source-separator-v42@e5ec94a85d0790edbdc5d2d4a683ffac5c0b3e34",
 },
 "corpus":{
   "v25_live_cells":len(LIVE),"ternary_classes":MOD3,
   "suffix_bits":SUFFIX_BITS,"train_motifs":list(TRAIN),
   "holdout_motifs":list(HOLDOUT),"cap":CAP,
 },
 "stats":dict(sorted(stats.items())),
 "train_feature_audit":train_audit,
 "selected_phase_feature":chosen,
 "holdout":hold_summary,
 "verdict":verdict,
 "interpretation":(
   "This gate conditions on exact source identity and the existing intrinsic "
   "Q2xQ3 cell, so any earned separator is genuinely return-phase information. "
   "D and rho are already present in the intrinsic cell; q and B are the "
   "remaining exact affine-law degrees of freedom."
 ),
 "promotion_boundary":(
   "A held-out separator only identifies the missing state coordinate on this "
   "bounded corpus. Global QED still requires a source-independent grammar "
   "theorem and V37 eventual-rank proof; do not infer finite law-bank completeness."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
