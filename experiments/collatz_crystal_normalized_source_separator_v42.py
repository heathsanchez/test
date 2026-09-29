#!/usr/bin/env python3
"""Crystal V42: normalized V23 source-fibre separator for V40 intrinsic cells.

V41 falsified V40's raw-source fibre.  Every V23 source already shares
2^59 * 3^8, so shallow residues of n are presentation.  The consequential
coordinate is the normalized parameter
    t = (n-N0)/(3^8*2^59).

This gate replays the exact V41 adversarial corpus but uses only V40 anchors
whose intrinsic Q2xQ3 representation is defined.  Three binary-tail motifs are
TRAIN and three are prospective HOLDOUT.

On TRAIN, find the smallest global pair (a,b) such that
    (V40 intrinsic cell, t mod 2^a, t mod 3^b)
has a functional next same-anchor consequence (next intrinsic cell or EXIT).
Freeze that pair and test it unchanged on HOLDOUT.

This is separator discovery / prospective falsification, not a universal proof.
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
        pat=[int(c) for c in name]
        return sum(pat[i%3]<<i for i in range(SUFFIX_BITS))
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

# Observation rows: (motif, t, intrinsic_state, consequence, metadata).
rows=[]
stats=Counter()
first_new_anchor=None
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
                    if first_new_anchor is None:
                        first_new_anchor={
                          "r":r,"a3":a3,"motif":motif,"t":str(t),
                          "source":str(n),"anchor":e["anchor"],
                          "k0":e["k0"],"k1":e["k1"],
                        }
                    continue
                e["ik"]=intrinsic(e)
                by[e["anchor"]].append(e)

            for anchor,es in by.items():
                es.sort(key=lambda z:(z["k0"],z["k1"]))
                for i,e in enumerate(es):
                    cons=("EXIT", rr["first_exit"]["kind"] if rr["first_exit"] else "CAP") if i+1==len(es) else ("NEXT",es[i+1]["ik"])
                    rows.append({
                      "motif":motif,"t":t,"state":e["ik"],"cons":cons,
                      "r":r,"a3":a3,"source":n,
                      "anchor":anchor,"k0":e["k0"],"k1":e["k1"],
                    })

stats["ROWS"]=len(rows)
train=[z for z in rows if z["motif"] in TRAIN]
hold=[z for z in rows if z["motif"] in HOLDOUT]
stats["TRAIN_ROWS"]=len(train); stats["HOLDOUT_ROWS"]=len(hold)

def residue_key(z,a,b):
    return (
      z["state"],
      z["t"]%(1<<a) if a else 0,
      z["t"]%(3**b) if b else 0,
    )

def conflicts(data,a,b):
    g=defaultdict(set); witness={}
    for z in data:
        k=residue_key(z,a,b)
        g[k].add(repr(z["cons"]))
        witness.setdefault(k,[]).append(z)
    bad={k:v for k,v in g.items() if len(v)>1}
    return bad,witness

candidates=[]
for a in range(BASE_DEPTH+SUFFIX_BITS+1):
    for b in range(5):
        bad,_=conflicts(train,a,b)
        if not bad:
            candidates.append((a+b,a,b))
assert candidates
_,A,B=min(candidates)
train_bad,train_w=conflicts(train,A,B)
assert not train_bad

# Prospective holdout: internal functionality plus agreement where a trained
# key is seen again.
train_cons={}
for z in train:
    k=residue_key(z,A,B)
    train_cons[k]=repr(z["cons"])

hold_groups=defaultdict(set); hold_rows=defaultdict(list)
for z in hold:
    k=residue_key(z,A,B)
    hold_groups[k].add(repr(z["cons"]))
    hold_rows[k].append(z)

hold_internal={k:v for k,v in hold_groups.items() if len(v)>1}
cross={}
for k,vs in hold_groups.items():
    if k in train_cons and (len(vs)!=1 or next(iter(vs))!=train_cons[k]):
        cross[k]=(train_cons[k],sorted(vs))

def pack_witness(k,wr,limit=4):
    out=[]
    for z in wr[k][:limit]:
        out.append({
          "motif":z["motif"],"t":str(z["t"]),"source":str(z["source"]),
          "r":z["r"],"a3":z["a3"],"anchor":z["anchor"],
          "depth":[z["k0"],z["k1"]],
          "state":repr(z["state"]),"consequence":repr(z["cons"]),
          "t_mod_2a":z["t"]%(1<<A) if A else 0,
          "t_mod_3b":z["t"]%(3**B) if B else 0,
        })
    return out

first_hold=None
if hold_internal:
    k=next(iter(hold_internal))
    first_hold={"kind":"HOLDOUT_INTERNAL_COLLISION","key":repr(k),
                "rows":pack_witness(k,hold_rows)}
elif cross:
    k=next(iter(cross))
    combined=defaultdict(list)
    for z in train+hold:
        if residue_key(z,A,B)==k: combined[k].append(z)
    first_hold={"kind":"TRAIN_HOLDOUT_CONSEQUENCE_MISMATCH","key":repr(k),
                "train_and_holdout":pack_witness(k,combined,8)}

# Also compute per-state minimal normalized parameter precision on TRAIN.
per_state={}
for state in sorted({z["state"] for z in train},key=repr):
    ds=[z for z in train if z["state"]==state]
    best=None
    for a in range(BASE_DEPTH+SUFFIX_BITS+1):
        for b in range(5):
            bad,_=conflicts(ds,a,b)
            if not bad:
                cand=(a+b,a,b)
                if best is None or cand<best: best=cand
    assert best
    per_state[repr(state)]={"a":best[1],"b":best[2],"rows":len(ds)}

verdict=(
  "NORMALIZED_PARAMETER_SEPARATOR_HOLDOUT_REJECTED"
  if hold_internal or cross else
  "NORMALIZED_PARAMETER_SEPARATOR_SURVIVES_HELD_OUT_MOTIFS"
)

result={
 "schema":"COLLATZ_CRYSTAL_NORMALIZED_SOURCE_SEPARATOR_V42",
 "parent":"collatz-crystal-v40-bank-challenge-v41@2283822c221f17cce47c954c203036c5138a0ae2",
 "corpus":{
   "v25_live_cells":len(LIVE),"ternary_classes":MOD3,
   "suffix_bits":SUFFIX_BITS,"train_motifs":list(TRAIN),
   "holdout_motifs":list(HOLDOUT),"cap":CAP,
 },
 "stats":dict(sorted(stats.items())),
 "frozen_global_separator":{
   "a_binary_parameter_bits":A,
   "b_ternary_parameter_trits":B,
   "mod2":1<<A if A else 1,
   "mod3":3**B,
   "train_functional":True,
 },
 "per_intrinsic_state_train_minima":per_state,
 "holdout":{
   "internal_collision_keys":len(hold_internal),
   "train_holdout_mismatch_keys":len(cross),
   "first_failure":first_hold,
 },
 "first_new_anchor_event":first_new_anchor,
 "verdict":verdict,
 "interpretation":(
   "Raw source residues are replaced by normalized V23 parameter residues. "
   "The selected pair is frozen using TRAIN only and prospectively checked "
   "on independent binary-tail motifs. New anchors remain a separate grammar "
   "completeness residual and are not hidden by this separator fit."
 ),
 "promotion_boundary":(
   "Even a green holdout is bounded evidence. QED requires a symbolic theorem "
   "that these normalized residues are sufficient for every lawful return "
   "and a complete treatment of anchors outside the frozen V40 bank."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
