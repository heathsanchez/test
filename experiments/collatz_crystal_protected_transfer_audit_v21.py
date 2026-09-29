#!/usr/bin/env python3
"""Crystal V21: protected-transfer audit of the V20 source-forced separator.

Purpose
-------
V20 found a striking bounded law on deterministic deficit-one four-thirds
types: for q>=52, the hardest normalized endpoint p_max=2n-3 always hits the
source-forced TERM_GT_B obstruction.  That is only useful for the live proof
residual if the obstruction is exposed while the source is still inside the
minimal-bad protected regime.

This audit therefore asks one causal question and nothing else:

    Did the source-forced separator fire before the concrete source had already
    produced a direct descent or a source-relative quarter-splice?

If not, the bounded V20 pattern is downstream consequence evidence and must
not be promoted as evidence for the hypothetical protected continuation.

No larger source range is introduced.  This replays exactly the V20
deterministic type boundary through qmin depth 100000.
"""
from collections import Counter
import json

H = 100_000
SOURCE_Q_MOD32 = {4, 9, 20, 25}
SOURCE_MOD24 = {3, 7, 15, 19}

def T(x: int) -> int:
    return (3*x+1)//2 if x & 1 else x//2

def v2(x: int) -> int:
    assert x > 0
    return (x & -x).bit_length()-1

def qmin_rows(H: int):
    p2=p3=1
    qm=0
    lag_q=0
    lag_B=0
    rows=[]
    for k in range(1,H+1):
        p2 <<= 1
        if p3 < p2:
            p3 *= 3
            qm += 1
        target=max(0,qm-1)
        if target == lag_q+1:
            lag_B=3*lag_B+(1<<(k-1))
            lag_q+=1
        assert target==lag_q
        q=qm-1
        if q<=0 or q%32 not in SOURCE_Q_MOD32:
            continue
        if q%4==0:
            n=3*q//4
        elif q%4==1:
            n=(3*q+1)//4
        else:
            continue
        if n%24 not in SOURCE_MOD24:
            continue
        D=(1<<k)-3**q
        assert D>0
        rows.append({
            "k":k,"q":q,"n":n,
            "near":lag_B>=D*n,
        })
    return rows

def source_forced_peel(n:int,k:int,q:int,p:int):
    threshold=(1<<k)*p
    C=n
    pow3=3**q
    positions=[]
    for j in range(q):
        if pow3*C >= threshold:
            return {"status":"B_NONPOS","step":j,"position":None}
        i=v2(C)
        if i>=k:
            return {"status":"POSITION_GE_K","step":j,"position":i}
        Cnext=3*C+(1<<i)
        pow3//=3
        positions.append(i)
        if pow3*Cnext > threshold:
            return {"status":"TERM_GT_B","step":j,"position":i}
        C=Cnext
    if C==threshold:
        return {"status":"OK","step":q,
                "position":positions[-1] if positions else None}
    return {"status":"RESIDUAL","step":q,
            "position":positions[-1] if positions else None}

def first_protected_failure(n:int, cap:int):
    x=n
    for depth in range(cap+1):
        if x<n:
            return {"kind":"DESCENT","depth":depth,"x":x}
        if x%8==5 and x<=4*n:
            return {"kind":"QUARTER_SPLICE","depth":depth,"x":x}
        if depth==cap:
            break
        x=T(x)
    return None

rows=qmin_rows(H)
near=[r for r in rows if r["near"]]

outcome=Counter()
term_transfer=Counter()
exception_rows=[]
closest_boundary=None
first_rows=[]

for r in near:
    k,q,n=r["k"],r["q"],r["n"]
    pmax=2*n-3
    peel=source_forced_peel(n,k,q,pmax)
    fail=first_protected_failure(n,k)

    if fail is None:
        outcome["STILL_PROTECTED_AT_BOUNDARY"] += 1
    else:
        outcome[fail["kind"]] += 1
        slack=k-fail["depth"]
        row={
            "k":k,"q":q,"n":n,"p_max":pmax,
            "peel_status":peel["status"],
            "peel_step":peel["step"],
            "forced_position":peel["position"],
            "protected_failure":fail,
            "boundary_slack":slack,
        }
        if closest_boundary is None or slack<closest_boundary["boundary_slack"]:
            closest_boundary=row
        if len(first_rows)<30:
            first_rows.append(row)

    if peel["status"]=="TERM_GT_B":
        pos=peel["position"]
        assert pos is not None
        fail_before_term=first_protected_failure(n,pos)
        if fail_before_term is None:
            term_transfer["TERM_WHILE_STILL_PROTECTED"] += 1
        else:
            term_transfer["PROTECTED_FAILURE_BEFORE_TERM"] += 1

    if peel["status"]!="TERM_GT_B":
        exception_rows.append({
            "k":k,"q":q,"n":n,"p_max":pmax,
            "peel_status":peel["status"],
            "peel_step":peel["step"],
            "forced_position":peel["position"],
            "protected_failure":fail,
        })

assert len(rows)==12501
assert len(near)==7669
assert outcome==Counter({"QUARTER_SPLICE":6346,"DESCENT":1323})
assert term_transfer==Counter({"PROTECTED_FAILURE_BEFORE_TERM":7665})
assert len(exception_rows)==4
assert [(r["q"],r["peel_status"]) for r in exception_rows]==[
    (4,"B_NONPOS"),(9,"POSITION_GE_K"),(36,"RESIDUAL"),(41,"POSITION_GE_K")
]
assert all(r["protected_failure"] is not None for r in exception_rows)
assert closest_boundary is not None
assert closest_boundary["n"]==27
assert closest_boundary["protected_failure"]=={
    "kind":"QUARTER_SPLICE","depth":56,"x":61
}
assert closest_boundary["boundary_slack"]==2

result={
    "schema":"COLLATZ_CRYSTAL_PROTECTED_TRANSFER_AUDIT_V21",
    "declared_boundary":{
        "qmin_depth":H,
        "relevant_types":len(rows),
        "near_resonant_types":len(near),
        "source_census":False,
        "larger_than_v20":False,
    },
    "protected_outcomes":dict(sorted(outcome.items())),
    "v20_term_transfer":dict(sorted(term_transfer.items())),
    "exceptions":exception_rows,
    "closest_protected_failure_to_boundary":closest_boundary,
    "first_rows":first_rows,
    "scientific_verdict":"V20_SEPARATOR_NOT_PROSPECTIVE_FOR_PROTECTED_RESIDUAL",
    "interpretation":(
        "Every concrete V20 near-resonant source exits the protected regime "
        "before its four-thirds deficit boundary. Every generic TERM_GT_B "
        "separator occurs only after that earlier exit. Therefore the bounded "
        "V20 zero is a downstream consequence of already-resolved sources and "
        "does not support universalization to a hypothetical minimal-bad "
        "protected continuation."
    ),
    "rejected_promotion":{
        "candidate":"FourThirdsDeficitSourceForcedTerm",
        "status":"REJECT_AS_TRANSFER_EVIDENCE",
        "mathematical_truth_status":"UNKNOWN",
    },
    "next_residual":{
        "name":"COUNTERFACTUAL_ZERO_TAIL_PROTECTED_SOURCE_COHERENCE",
        "statement":(
            "reason directly inside the hypothetical fixed-source, zero-tail, "
            "no-OrdinaryExit continuation. Actual resolved-source traces cannot "
            "supply the missing separator after their first protected failure."
        ),
        "universal":"UNKNOWN",
    },
    "global_collatz":"UNKNOWN",
}
print(json.dumps(result,indent=2))
