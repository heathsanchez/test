#!/usr/bin/env python3
"""Crystal V41: adversarial completeness challenge for the V40 return bank.

Parent V40 found a 13-cell acyclic phase-normalized same-anchor return graph on
the frozen V36/V26 hard sources.  This gate does NOT promote that finite graph.
It tries to falsify its completeness on exact members of the sole V23 family.

Start from every V25 depth-9 live parameter residue r (64 exact cylinders).
Cross it with every source ternary fibre a mod 3^4 (81 classes), then append
several deterministic adversarial binary suffix motifs.  CRT gives one exact
natural parameter t in each combined congruence class.

For each source n(t), parse only post-zero-tail exact same-anchor returns using
the V40 semantics.  Classify each return in the *frozen V40 bank*.  Emit:
  NEW_CELL             -- protected source-biadic key absent from V40;
  SUCCESSOR_COLLISION  -- known key has a new lawful next key;
  TERMINAL_REOPEN      -- a V40 terminal key has a later same-anchor return;
  NEW_RETURN_LAW       -- exact same-anchor affine law absent from frozen bank.

One witness rejects frozen-bank completeness.  No bounded survival can prove
universality.
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

def live_frontier(depth:int):
    frontier=[0]
    for d in range(depth+1):
        survivors=[]
        nxt=[]
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
assert len(LIVE)==64, len(LIVE)

def motif_bits(name:str):
    if name=="ZERO":
        return 0
    if name=="ONES":
        return (1<<SUFFIX_BITS)-1
    if name in ("110","101","011"):
        pat=[int(c) for c in name]
        x=0
        for i in range(SUFFIX_BITS):
            x |= pat[i%3]<<i
        return x
    if name=="ALT01":
        return sum((i&1)<<i for i in range(SUFFIX_BITS))
    raise KeyError(name)

MOTIFS=("ZERO","ONES","110","101","011","ALT01")
M2=1<<(BASE_DEPTH+SUFFIX_BITS)
INV2=pow(M2,-1,MOD3)

def crt_parameter(r:int,a:int,motif:str):
    suffix=motif_bits(motif)
    t2=r+(suffix<<BASE_DEPTH)
    assert t2 % (1<<BASE_DEPTH)==r
    k=((a-t2)*INV2)%MOD3
    t=t2+M2*k
    assert t%M2==t2
    assert t%MOD3==a
    return t

def law_key(e):
    c=e["cert"]
    return (e["anchor"],c["A"],c["B"],c["D"],c["rho"])

# Freeze V40 exact law/cell/edge authority.
ref_laws=set()
ref_nodes=set()
ref_succ=defaultdict(set)
for rr in v40.runs:
    by=defaultdict(list)
    for e in rr["events"]:
        ref_laws.add(law_key(e))
        e["intrinsic_key"],e["source_key"]=v40.event_keys(e)
        ref_nodes.add(e["source_key"])
        by[e["anchor"]].append(e)
    for anchor,es in by.items():
        es.sort(key=lambda z:(z["k0"],z["k1"]))
        for x,y in zip(es,es[1:]):
            ref_succ[x["source_key"]].add(y["source_key"])
for n in ref_nodes:
    ref_succ.setdefault(n,set())

counts=Counter()
first={}
new_cells=set()
new_laws=set()
new_edges=set()
new_anchors=set()
max_d2=0
max_r3=0
tested=0
exit_counts=Counter()

for r in LIVE:
    for a in range(MOD3):
        for motif in MOTIFS:
            t=crt_parameter(r,a,motif)
            n=v25.N0+v25.NC*t
            rr=v40.actual_episode_returns(
                f"r{r}-a{a}-{motif}",n,CAP
            )
            tested+=1
            if rr["first_exit"] is not None:
                exit_counts[rr["first_exit"]["kind"]]+=1
            if rr["note"]=="ordinary exit before zero-tail":
                counts["EXIT_PRE_ZERO"]+=1
                continue
            counts["POST_ZERO_SOURCES"]+=1

            by=defaultdict(list)
            for e in rr["events"]:
                lk=law_key(e)

                # A new episode anchor is already an exact separator against
                # the frozen V40 grammar.  Do not crash trying to classify it
                # through a Q3 bank that was never learned for this anchor.
                if e["anchor"] not in v40.banks:
                    counts["NEW_ANCHOR"]+=1
                    new_anchors.add(e["anchor"])
                    if lk not in ref_laws:
                        counts["NEW_RETURN_LAW"]+=1
                        new_laws.add(lk)
                    first.setdefault("NEW_ANCHOR",{
                        "r":r,"a":a,"motif":motif,"t":str(t),"source":str(n),
                        "anchor":e["anchor"],"k0":e["k0"],"k1":e["k1"],
                        "law":repr(lk),
                    })
                    first.setdefault("NEW_RETURN_LAW",{
                        "r":r,"a":a,"motif":motif,"t":str(t),"source":str(n),
                        "k0":e["k0"],"k1":e["k1"],
                        "law":repr(lk),"source_key":"UNCLASSIFIED_NEW_ANCHOR",
                    })
                    continue

                e["intrinsic_key"],e["source_key"]=v40.event_keys(e)
                key=e["source_key"]
                ik=e["intrinsic_key"]
                d2=ik[1]; r3=ik[3]
                max_d2=max(max_d2,d2)
                if r3 is not None:
                    max_r3=max(max_r3,r3)
                by[e["anchor"]].append(e)

                if lk not in ref_laws:
                    counts["NEW_RETURN_LAW"]+=1
                    new_laws.add(lk)
                    first.setdefault("NEW_RETURN_LAW",{
                        "r":r,"a":a,"motif":motif,"t":str(t),"source":str(n),
                        "k0":e["k0"],"k1":e["k1"],
                        "law":repr(lk),"source_key":repr(key),
                    })
                if key not in ref_nodes:
                    counts["NEW_CELL"]+=1
                    new_cells.add(key)
                    first.setdefault("NEW_CELL",{
                        "r":r,"a":a,"motif":motif,"t":str(t),"source":str(n),
                        "k0":e["k0"],"k1":e["k1"],
                        "source_key":repr(key),"intrinsic_key":repr(ik),
                        "law":repr(lk),
                    })

            for anchor,es in by.items():
                es.sort(key=lambda z:(z["k0"],z["k1"]))
                for x,y in zip(es,es[1:]):
                    akey=x["source_key"]; bkey=y["source_key"]
                    if akey in ref_nodes and bkey not in ref_succ[akey]:
                        tag="TERMINAL_REOPEN" if not ref_succ[akey] else "SUCCESSOR_COLLISION"
                        counts[tag]+=1
                        new_edges.add((akey,bkey))
                        first.setdefault(tag,{
                            "r":r,"a":a,"motif":motif,"t":str(t),
                            "source":str(n),"anchor":anchor,
                            "from":repr(akey),"to":repr(bkey),
                            "from_depth":[x["k0"],x["k1"]],
                            "to_depth":[y["k0"],y["k1"]],
                        })

# Positive controls ensure the frozen hard sources still classify.
for rr in v40.runs:
    for e in rr["events"]:
        _ik,sk=v40.event_keys(e)
        assert sk in ref_nodes
        assert law_key(e) in ref_laws

rejected=any(counts[k] for k in
             ("NEW_ANCHOR","NEW_CELL","SUCCESSOR_COLLISION","TERMINAL_REOPEN","NEW_RETURN_LAW"))
verdict=("FROZEN_V40_BANK_COMPLETENESS_REJECTED"
         if rejected else
         "NO_FALSIFIER_IN_ADVERSARIAL_V25xQ3_CHALLENGE")

result={
  "schema":"COLLATZ_CRYSTAL_V40_BANK_CHALLENGE_V41",
  "parent":"collatz-crystal-phase-normalized-return-v40@66bd8e707e00f5124d5201a81814a0ea47b2fdee",
  "challenge":{
    "v25_depth":BASE_DEPTH,
    "v25_live_binary_cells":len(LIVE),
    "ternary_classes":MOD3,
    "suffix_bits":SUFFIX_BITS,
    "motifs":list(MOTIFS),
    "exact_sources_tested":tested,
    "crt_modulus_bits":BASE_DEPTH+SUFFIX_BITS,
  },
  "frozen_v40_bank":{
    "laws":len(ref_laws),
    "source_cells":len(ref_nodes),
    "edges":sum(len(v) for v in ref_succ.values()),
  },
  "counts":dict(sorted(counts.items())),
  "exit_counts":dict(sorted(exit_counts.items())),
  "distinct_new_anchors":len(new_anchors),
  "new_anchors":sorted(new_anchors),
  "distinct_new_laws":len(new_laws),
  "distinct_new_cells":len(new_cells),
  "distinct_new_edges":len(new_edges),
  "max_observed_d2":max_d2,
  "max_observed_r3_against_frozen_bank":max_r3,
  "first_falsifiers":first,
  "verdict":verdict,
  "interpretation":(
    "This is an adversarial bounded falsifier over exact V23 congruence "
    "subfamilies. One new law/cell/edge rejects the frozen 13-law bank. "
    "Absence of a falsifier would still not prove all-depth completeness."
  ),
  "promotion_boundary":(
    "A complete QED bank must be derived symbolically from the lawful return "
    "grammar / V38-normalized continuation, not inferred from finite source "
    "coverage."
  ),
  "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
