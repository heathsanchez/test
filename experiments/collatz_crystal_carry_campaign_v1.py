#!/usr/bin/env python3
"""Stateful Crystal carry campaign.

Cycles preserve epistemic boundaries. This script does NOT manufacture an
aggregate (j,m) successor graph. It rotates representations when a candidate is
falsified and emits the smallest exact theorem/obstruction at the stop condition.
"""
import json
from fractions import Fraction
from collections import defaultdict

RHO=Fraction(511,512)

def synthetic_late_singleton_fixture():
    # Qualified 24-bit holdout has fixed-21 failures at j=250..253, live=1.
    return {"depths":[250,251,252,253],"live":1,"wait":37,
            "authority":"run36316349693 -> adaptive recovery run36316411307"}

def promotion_allowed(candidate):
    return candidate.get("derivation") not in {"next_observed_exit","finite_only","aggregate_fake_successor"}

def bad_kernel(nodes):
    assert all(n.get("successors") is not None for n in nodes), "exact successor relation required"
    ids={n["id"] for n in nodes}; bad={n["id"] for n in nodes if n.get("bad",True)}
    changed=True
    while changed:
        changed=False
        for n in nodes:
            if n["id"] in bad and not any(s in bad for s in n["successors"] if s in ids):
                bad.remove(n["id"]); changed=True
    return sorted(bad)

def epistemic_status(empty,universal):
    if empty and universal:return "UNIVERSAL_BAD_KERNEL_EMPTY"
    if empty:return "BOUNDED_BAD_KERNEL_EMPTY"
    return "BAD_KERNEL_SURVIVES"

def qmin(depth):
    out=[0]*(depth+1);q=0;p=1
    for j in range(1,depth+1):
        while p < 1<<j:p*=3;q+=1
        out[j]=q
    return out

def exact_prefix_states(depth):
    """Exact canonical source cylinders (q,R,Y) surviving coefficient boundary."""
    qm=qmin(depth); st=[(0,0,0)]; levels=[st]
    for j in range(1,depth+1):
        nx=[]
        for q,R,Y in st:
            for bit in (0,1):
                lift=(bit-Y)&1
                Rp=R+(lift<<(j-1)); z=Y+(3**q)*lift
                Yp=(3*z+1)//2 if bit else z//2
                qp=q+bit
                if qp>=qm[j]: nx.append((qp,Rp,Yp))
        st=nx; levels.append(st)
    return levels

def signature(s,j,width):
    q,R,Y=s
    mask=(1<<min(j,width))-1
    # earned exact coordinates only: source prefix, endpoint prefix, q excess.
    return (R&mask,Y&mask,q-qmin(j)[j])

def cycle_campaign(max_depth=18):
    cycles=[]
    # C1 preserve falsifications.
    f=synthetic_late_singleton_fixture()
    cycles.append({"cycle":1,"action":"reject-fixed-horizon","result":f,
      "promotion":"REJECT fixed b<=21; adaptive waiting remains CANDIDATE"})
    # C2 exact transported cylinders, no aggregate fake edges.
    levels=exact_prefix_states(max_depth)
    cycles.append({"cycle":2,"action":"construct-exact-live-source-cylinders",
      "depth":max_depth,"live_states":len(levels[-1]),
      "transition_authority":"canonical lift recursion (q,R,Y)",
      "promotion":"EXACT_FINITE_MODEL"})
    # C3 dynamically refine quotient widths. Protected future = survival profile
    # over exact descendants, not observed integer-source exit.
    chosen=1; history=[]
    for width in range(1,min(12,max_depth)+1):
        groups=defaultdict(list)
        for s in levels[-1]:groups[signature(s,max_depth,width)].append(s)
        # Future consequence available in this finite exact model: exact identity
        # of next-level legal children cannot be checked past max_depth, so use
        # current multiplicity only as separator discovery, never proof.
        collisions=sum(len(v)-1 for v in groups.values())
        history.append({"width":width,"classes":len(groups),"collision_excess":collisions})
        chosen=width
        if collisions==0:break
    cycles.append({"cycle":3,"action":"separator-refinement",
      "history":history,"chosen_width":chosen,
      "promotion":"DISCOVERY_ONLY; injectivity is not contraction"})
    # C4 theorem audit: can finite cylinder injectivity establish adaptive waiting?
    candidate={"derivation":"finite_only","width":chosen}
    ok=promotion_allowed(candidate)
    cycles.append({"cycle":4,"action":"promotion-audit","candidate":candidate,
      "allowed":ok,"result":"REJECT" if not ok else "CANDIDATE"})
    # C5 expose exact residual instead of pretending SCC.
    residual={
      "name":"ALL_DEPTH_LIVE_ORIGIN_CARRY_LOSS",
      "statement":"derive finite adaptive normalized contraction waiting from exact source/carry recursion without assuming a future coefficient crossing",
      "needed_for_bad_graph":"an all-depth quotient/transition law mapping exact transported source cylinders to finitely represented consequential carry states",
      "known_separator":"fixed 21-step horizon fails on late singleton live cylinders",
      "bounded_positive":"24-bit full odd-source holdout: adaptive rho=511/512, max selected block 37, zero bad roots",
      "universal":"UNKNOWN"}
    cycles.append({"cycle":5,"action":"stop-at-irreducible-obstruction","residual":residual})
    return {"schema":"COLLATZ_CRYSTAL_CARRY_CAMPAIGN_V1","cycles":cycles,
      "stop_reason":"No exact finite all-depth carry quotient/successor theorem exists in current warranted inputs; SCC computation before it would be fabricated.",
      "final_residual":residual,"global_collatz":"UNKNOWN"}

if __name__=="__main__":print(json.dumps(cycle_campaign(),indent=2))
