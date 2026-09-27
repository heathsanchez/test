#!/usr/bin/env python3
"""Crystal boundary-bias majorization V1.

At a first coefficient crossing d=e+1, every earlier prefix survives, so the
actual odd-count prefix sums dominate qmin. The total at e is exactly qmin(e).
Hence the actual odd positions are componentwise no later than the deterministic
boundary positions. Since the affine bias is
    B = sum_j 3^(q-1-j) 2^(p_j),
moving any odd position earlier can only decrease B.
Thus the mechanical qmin boundary word gives a universal worst-case bias for
the first-crossing prefix.

This script independently replays that finite combinatorial implication on all
binary words through a declared small depth, then scans the exact mechanical
cap C_d=floor(B*/(2^d-3^q)) at all boundary-jump depths. It is theorem-discovery
and regression evidence; the all-depth majorization argument is mathematical,
while the depth scan is finite.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path

def qmin_data(H:int):
    p2=p3=1; q=0
    qm=[0]*(H+1); bits=[0]*H
    for t in range(1,H+1):
        p2*=2
        old=q
        if p3<p2:
            p3*=3; q+=1
        assert q-old in (0,1)
        qm[t]=q
        bits[t-1]=q-old
        assert p2<=p3<3*p2
    return qm,bits

def bias(bits):
    B=0
    for t,b in enumerate(bits):
        if b:
            B=3*B+(1<<t)
    return B

def odd_positions(bits):
    return [i for i,b in enumerate(bits) if b]

def dominates_qmin(bits,qm):
    q=0
    for t,b in enumerate(bits,1):
        q+=b
        if q<qm[t]: return False
    return q==qm[len(bits)]

def exhaustive_majorization(max_e:int):
    qm, mech=qmin_data(max_e)
    checked=0
    worst_gap=None
    for e in range(1,max_e+1):
        mbits=mech[:e]
        mpos=odd_positions(mbits)
        mb=bias(mbits)
        for mask in range(1<<e):
            bits=[(mask>>i)&1 for i in range(e)]
            if not dominates_qmin(bits,qm):
                continue
            apos=odd_positions(bits)
            assert len(apos)==len(mpos)
            assert all(a<=m for a,m in zip(apos,mpos)), (e,apos,mpos)
            ab=bias(bits)
            assert ab<=mb,(e,bits,ab,mb)
            gap=mb-ab
            if worst_gap is None or gap>worst_gap[0]:
                worst_gap=(gap,e,mask,ab,mb)
            checked+=1
    return {"max_depth":max_e,"admissible_words_checked":checked,
            "max_bias_gap":None if worst_gap is None else worst_gap[0]}

def scan(H:int):
    p2=p3=1; q=B=0
    jump_depths=0; large_elim=0
    maxcap=0; maxrow=None; records=[]
    cap_digest=hashlib.sha256()
    for e in range(1,H+1):
        p2 <<= 1
        if p3<p2:
            p3*=3; q+=1
            B=3*B+(p2>>1)
        # First crossing at d=e+1 requires the threshold to rise there.
        if p3 < (p2<<1):
            d=e+1
            D=(p2<<1)-p3
            cap=B//D
            jump_depths+=1
            if cap<=q: large_elim+=1
            cap_digest.update(f"{d},{q},{cap}\n".encode())
            if cap>maxcap:
                maxcap=cap
                maxrow={"depth":d,"q":q,"cap":cap}
                records.append(maxrow.copy())
    return {
      "depth":H,
      "jump_depths":jump_depths,
      "large_source_branch_eliminated_by_cap_le_q":large_elim,
      "large_source_branch_resonant_depths":jump_depths-large_elim,
      "max_mechanical_nondescending_source_cap":maxcap,
      "maximizing_record":maxrow,
      "record_count":len(records),
      "last_records":records[-12:],
      "cap_rows_sha256":cap_digest.hexdigest(),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=500000)
    ap.add_argument("--exhaustive-depth",type=int,default=18)
    ap.add_argument("--out",type=Path)
    A=ap.parse_args()
    assert 2<=A.exhaustive_depth<=20
    exact=exhaustive_majorization(A.exhaustive_depth)
    finite=scan(A.depth)
    # Regression at the prior canonical horizon.
    prior=scan(271782)
    assert prior["jump_depths"]==171475
    assert prior["large_source_branch_eliminated_by_cap_le_q"]==118169
    assert prior["max_mechanical_nondescending_source_cap"]==5205340379
    assert prior["maximizing_record"]=={"depth":125743,"q":79335,"cap":5205340379}
    result={
      "schema":"COLLATZ_BOUNDARY_BIAS_MAJORIZATION_V1",
      "majorization_law":{
        "premise":"first-crossing prefix survives at every proper depth and has q_e=qmin(e)",
        "consequence":"actual odd positions are componentwise no later than qmin-boundary positions, hence bias_actual <= bias_boundary",
        "local_exchange":"01 -> 10 decreases final affine bias, including after any common suffix",
        "status":"EXACT_COMBINATORIAL_ARGUMENT_WITH_EXHAUSTIVE_REGRESSION_AND_LEAN_LOCAL_EXCHANGE",
      },
      "exhaustive_regression":exact,
      "prior_canonical_horizon":prior,
      "extended_scan":finite,
      "interpretation":"At a hard first crossing, n <= mechanical_cap. If q<n, every depth with cap<=q is impossible. cap>q depths are the remaining near-resonant large-source branch; the n<=q origin branch remains separate.",
      "not_proved":["origin-branch constructor coverage","all-depth elimination of resonant cap>q depths","Collatz"],
      "global_collatz":"UNKNOWN",
    }
    txt=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if A.out:
        A.out.parent.mkdir(parents=True,exist_ok=True);A.out.write_text(txt)
    print(txt,end="")
if __name__=="__main__": main()
