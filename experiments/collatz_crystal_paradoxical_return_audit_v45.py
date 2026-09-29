#!/usr/bin/env python3
"""V45: paradoxical same-anchor return audit over the full V41 challenge.

After V42/V44, deterministic next-cell prediction is retired.  V37 only needs
eventual rank progress.  This gate therefore asks a weaker, rank-relevant
question for every exact post-zero-tail same-anchor return in the adversarial
31,104-source V41 corpus.

For a return
    m' = (A*m+B)/2^D
with C=2^D-A>0, non-descent is possible exactly when
    m <= B/C.
Because a live anchor x=2^r*m-1 has not triggered the direct-descent exit,
x >= source >= V23.N0, hence
    m >= ceil((N0+1)/2^r).
So B/C below this V23 live floor proves strict descent for the entire V23 live
domain of that law, independently of future-state determinism.

We census:
  * coefficient-contracting laws and their exact fixed points;
  * any law whose fixed point reaches the V23 live floor;
  * actual paradoxical returns (contracting coefficient but m' >= m);
  * coefficient-noncontracting returns;
  * the V38 sparse 12-odd / >=20-step subfamily.

This is a bounded theorem-discovery/falsifier gate.  It does not establish
all-depth return-grammar completeness.
"""
from __future__ import annotations
from collections import Counter
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

BASE_DEPTH=9
SUFFIX_BITS=18
CAP=700
MOD3=3**4
MOTIFS=("ZERO","ONES","110","101","011","ALT01")

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

def pow3_exp(a:int):
    q=0
    while a>1 and a%3==0:
        a//=3; q+=1
    assert a==1
    return q

def ceil_div(a:int,b:int):
    return (a+b-1)//b

def law_key(e):
    c=e["cert"]
    return (e["anchor"],c["A"],c["B"],c["D"],c["rho"])

stats=Counter()
laws={}
bad_floor_laws={}
actual_paradoxical=[]
noncontracting=[]
sparse=[]
first_by_class={}
tested=0

for r in LIVE:
    for a3 in range(MOD3):
        for motif in MOTIFS:
            t=crt_parameter(r,a3,motif)
            n=v25.N0+v25.NC*t
            rr=v40.actual_episode_returns(f"r{r}-a{a3}-{motif}",n,CAP)
            tested+=1
            if rr["note"]=="ordinary exit before zero-tail":
                stats["EXIT_PRE_ZERO"]+=1
                continue
            stats["POST_ZERO_SOURCES"]+=1
            for e in rr["events"]:
                stats["RETURN_EVENTS"]+=1
                c=e["cert"]; A=c["A"]; B=c["B"]; D=c["D"]; anchor=e["anchor"]
                q=pow3_exp(A)
                x0=(1<<anchor)*e["m0"]-1
                x1=(1<<anchor)*e["m1"]-1
                # No direct-descent exit occurred before this live return.
                assert x0 >= n
                key=law_key(e)
                C=(1<<D)-A
                row={
                  "law":repr(key),"anchor":anchor,"A":str(A),"B":str(B),"D":D,
                  "q":q,"rho":str(c["rho"]),"source":str(n),"t":str(t),
                  "motif":motif,"depth":[e["k0"],e["k1"]],
                  "m0":str(e["m0"]),"m1":str(e["m1"]),
                  "x0":str(x0),"x1":str(x1),
                }
                if C>0:
                    stats["CONTRACTING_EVENTS"]+=1
                    fp=Fraction(B,C)
                    v23_floor=ceil_div(v25.N0+1,1<<anchor)
                    source_floor=ceil_div(n+1,1<<anchor)
                    row.update({
                      "fixed_point":[fp.numerator,fp.denominator],
                      "v23_live_m_floor":str(v23_floor),
                      "source_live_m_floor":str(source_floor),
                      "fixed_point_reaches_v23_floor":fp>=v23_floor,
                      "actual_nondescending":e["m1"]>=e["m0"],
                    })
                    old=laws.get(key)
                    if old is None:
                        laws[key]=row
                    if fp>=v23_floor:
                        bad_floor_laws.setdefault(key,row)
                        first_by_class.setdefault("FIXED_POINT_REACHES_V23_FLOOR",row)
                    if e["m1"]>=e["m0"]:
                        stats["ACTUAL_PARADOXICAL_EVENTS"]+=1
                        if len(actual_paradoxical)<30: actual_paradoxical.append(row)
                        first_by_class.setdefault("ACTUAL_PARADOXICAL",row)
                    else:
                        stats["ACTUAL_CONTRACTING_DESCENT_EVENTS"]+=1
                    if q==12 and D>=20:
                        stats["V38_SPARSE_EVENTS"]+=1
                        if len(sparse)<20: sparse.append(row)
                else:
                    stats["NONCONTRACTING_EVENTS"]+=1
                    row["slope_class"]="UNIT" if C==0 else "EXPANDING"
                    if len(noncontracting)<30: noncontracting.append(row)
                    first_by_class.setdefault("NONCONTRACTING",row)

# Law-level census only for coefficient-contracting laws.
stats["DISTINCT_CONTRACTING_LAWS"]=len(laws)
stats["DISTINCT_CONTRACTING_LAWS_REACHING_V23_FLOOR"]=len(bad_floor_laws)

# Rank the most dangerous contracting laws by exact fixed point / V23 floor.
danger=[]
for row in laws.values():
    p,u=row["fixed_point"]
    floor=int(row["v23_live_m_floor"])
    ratio=Fraction(p,u*floor)
    danger.append((ratio,row))
danger.sort(key=lambda z:z[0],reverse=True)
top=[]
for ratio,row in danger[:30]:
    z=dict(row)
    z["fixed_point_over_v23_floor"]=[ratio.numerator,ratio.denominator]
    top.append(z)

if actual_paradoxical:
    verdict="ACTUAL_PARADOXICAL_RETURN_SEPARATOR"
elif bad_floor_laws:
    verdict="POTENTIAL_PARADOXICAL_LAWS_REACH_LIVE_FLOOR"
else:
    verdict="ALL_OBSERVED_CONTRACTING_RETURN_LAWS_DESCEND_ON_V23_LIVE_DOMAIN"

result={
  "schema":"COLLATZ_CRYSTAL_PARADOXICAL_RETURN_AUDIT_V45",
  "parents":{
    "V41":"collatz-crystal-v40-bank-challenge-v41@2283822c221f17cce47c954c203036c5138a0ae2",
    "V44":"collatz-crystal-return-phase-separator-v44@236e02a4e4161ff027922fa1e3024b0febb8c0f7",
  },
  "challenge":{
    "v25_depth":BASE_DEPTH,"live_binary_cells":len(LIVE),
    "ternary_classes":MOD3,"suffix_bits":SUFFIX_BITS,
    "motifs":list(MOTIFS),"exact_sources_tested":tested,"cap":CAP,
  },
  "stats":dict(sorted(stats.items())),
  "first_by_class":first_by_class,
  "actual_paradoxical_examples":actual_paradoxical,
  "top_contracting_laws_by_fixed_point_over_v23_floor":top,
  "noncontracting_examples":noncontracting,
  "v38_sparse_examples":sparse,
  "verdict":verdict,
  "interpretation":(
    "This gate tests well-founded progress directly rather than future-state "
    "determinism. For every contracting affine return law, B/(2^D-A) is the "
    "exact non-descent threshold. Comparing it with the source-independent "
    "V23 live floor isolates whether that law can support a live paradoxical "
    "same-anchor return at all."
  ),
  "promotion_boundary":(
    "A green bounded census is not universal. QED would require an all-depth "
    "theorem covering every lawful return word, or a reduction showing every "
    "infinite ZeroTailLive continuation necessarily encounters a contracting "
    "return whose fixed point is below its live floor, feeding V37 hprogress."
  ),
  "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
