#!/usr/bin/env python3
"""Adaptive Q3 residual refinement for the first dangerous Collatz Farey rung.

The first-difference audit intentionally stopped at the first non-centre trit.
This experiment applies the ROS residual-refinement rule instead: every
uncertified first-difference cylinder is refined by later Q3 digits until the
absolute endpoint precision R (least R with 3^R above the whole live interval).

No new certificate family is introduced.  At each new trit we test only:
  * exact interval emptiness;
  * a NEW direct reverse certificate whose length is exactly the new depth;
  * a NEW odd one-forward-then-reverse certificate whose reverse length is
    exactly depth+1.

Why only the new lengths?  A residual parent at depth j-1 has already ruled
out every shorter certificate, and its newly exposed trit cannot change the
transported residues at those shorter precisions.

If anything survives at absolute depth R, each leaf contains at most one
ordinary endpoint in the certified interval and is emitted explicitly.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from collections import Counter,defaultdict

import collatz_absolute_q3_range_v0 as aq
import collatz_reverse_trit_separator_v0 as v0
import collatz_reverse_trit_bicell_v1 as v1
import collatz_transfer_farey as farey


def direct_new_cert(r:int,j:int,L:int,G:int):
    den=3**j
    budget=den.bit_length()-1
    if budget<j:
        return None
    w=v0.contracting_word(j,r%den,budget)
    if w is None:
        return None
    S,C=v0.cocycle(w)
    lead=1<<S
    gap=den-lead
    if gap<=0:
        return None
    positive=lead*L-C
    margin=gap*L+C-den*G
    if positive<=0 or margin<=0:
        return None
    return dict(kind="DIRECT_REVERSE_NEW",odd_inverse_steps=j,
                actions=list(w),S=S,C=C,residue=r%den,modulus=den,
                uniform_margin_at_L=margin)


def odd_one_forward_new_cert(r:int,j:int,L:int,G:int):
    """Only the newly available reverse precision o=j+1."""
    prec=j+1
    P=3**prec
    zres=((3*r+1)*pow(2,-1,P))%P
    o=prec
    if o<=1:
        return None
    # Same exact budget as V1 odd mode:
    # 3*2^(S-1) < 3^o <=> 2^(S-1) < 3^(o-1).
    budget=(3**(o-1)).bit_length()
    if budget<o:
        return None
    ro=zres
    w=v0.contracting_word(o,ro,budget)
    if w is None:
        return None
    S,C=v0.cocycle(w)
    if S<1:
        return None
    h=1<<(S-1)
    den=3**o
    lead=3*h
    gap=den-lead
    positive=lead*L+h-C
    margin=gap*L+C-h-den*G
    if gap<=0 or positive<=0 or margin<=0:
        return None
    return dict(kind="ONE_FORWARD_THEN_REVERSE_NEW",
                odd_inverse_steps=o,actions=list(w),S=S,C=C,
                transported_residue=ro,transported_modulus=den,
                uniform_margin_at_L=margin)


def run(output:Path,max_nodes:int):
    L=farey.L
    U=farey.dk_live_ceiling_int
    G=farey.live_gap_ceiling
    R=aq.least_q3_depth_above(U)
    assert R==46
    aq.configure(farey.q1,farey.t1,L,G,R)

    base=aq.classify_rung("rung1",farey.q1,farey.t1,L,U,G)
    initials=defaultdict(list)
    for x in base["residual_cells"]:
        assert x["parity"]==1
        initials[x["depth"]].append((x["residue"],x["parity"],
                                      x["first_difference_depth"]))

    active=[]
    rows=[]
    closure=Counter()
    leaf_witnesses=[]
    total_tested=0

    for j in range(1,R+1):
        # Existing unresolved cells from depth j-1 split by the next trit.
        candidates=[]
        if active:
            step=3**(j-1)
            for r,parity,fd in active:
                for digit in range(3):
                    candidates.append((r+digit*step,parity,fd))
        # Add cylinders whose first difference is exposed exactly here.
        candidates.extend(initials.get(j,()))
        # All cylinders at a common depth are disjoint; deduplicate defensively.
        seen=set(); uniq=[]
        for z in candidates:
            key=(z[0]%(3**j),z[1])
            if key in seen:
                raise AssertionError(("duplicate cell",j,key,z))
            seen.add(key);uniq.append(z)
        candidates=uniq

        next_active=[]
        local=Counter()
        for r,parity,fd in candidates:
            total_tested+=1
            y=aq.first_in_cell(L,U,r,j,parity)
            if y is None:
                kind="RANGE_EMPTY";cert=None
            else:
                cert=direct_new_cert(r,j,L,G)
                if cert is not None:
                    kind=cert["kind"]
                else:
                    assert parity==1
                    cert=odd_one_forward_new_cert(r,j,L,G)
                    if cert is not None:
                        kind=cert["kind"]
                    else:
                        kind="RESIDUAL"
            local[kind]+=1;closure[kind]+=1
            if kind=="RESIDUAL":
                next_active.append((r%(3**j),parity,fd))
                if j==R:
                    # Since 2*3^R exceeds the whole interval, this is unique.
                    assert y is not None
                    leaf_witnesses.append(dict(
                        endpoint=y,residue=r%(3**j),modulus=3**j,
                        parity=parity,first_difference_depth=fd))
        active=next_active
        row=dict(depth=j,input_cells=len(candidates),
                 residual=len(active),counts=dict(sorted(local.items())))
        rows.append(row)
        if candidates or initials.get(j):
            print("REFINE_LEVEL",json.dumps(row,sort_keys=True))
        if len(active)>max_nodes:
            result=dict(schema="COLLATZ_Q3_RESIDUAL_REFINEMENT_V1",
                absolute_depth=R,rows=rows,total_tested=total_tested,
                final_residual=len(active),verdict="ABORT_NODE_LIMIT",
                max_nodes=max_nodes)
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
            print("VERDICT ABORT_NODE_LIMIT")
            return

    assert len(active)==len(leaf_witnesses)
    result=dict(
        schema="COLLATZ_Q3_RESIDUAL_REFINEMENT_V1",
        parent="collatz-absolute-q3-range-v0",
        lower=L,upper=U,gap=G,absolute_depth=R,
        initial_residual_cylinders=sum(len(v) for v in initials.values()),
        rows=rows,total_tested=total_tested,
        closure_counts=dict(sorted(closure.items())),
        final_residual=len(active),
        explicit_endpoint_witnesses=leaf_witnesses,
        verdict=("PASS_ALL_Q3_RESIDUALS_CLOSE"
                 if not active else "EXACT_ABSOLUTE_ENDPOINT_RESIDUALS_REMAIN"),
        scope=("rung1 certified interval; residual-driven Q3 refinement to "
               "absolute depth; existing direct/one-forward reverse certificate "
               "family only; no Collatz claim")
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL_RESIDUAL",len(active))
    for x in leaf_witnesses[:100]:
        print("ENDPOINT_RESIDUAL",json.dumps(x,sort_keys=True))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--max-nodes",type=int,default=2000000)
    a=ap.parse_args()
    run(a.output,a.max_nodes)
