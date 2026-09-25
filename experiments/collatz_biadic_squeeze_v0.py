#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path
import collatz_biadic_cell_v0 as bc
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base

G=4142380787
B=20
assert 2*3**B>G and 2*3**(B-1)<=G

def v2z(x):
    x=abs(int(x))
    return None if x==0 else (x & -x).bit_length()-1

def vpz(x,p):
    x=abs(int(x))
    if x==0:return None
    v=0
    while x%p==0:x//=p;v+=1
    return v

def threshold_frontier():
    out=[]
    for a in range(40):
        for b in range(30):
            M=(1<<a)*3**b
            if M<=G: continue
            if (a==0 or (1<<(a-1))*3**b<=G) and (b==0 or (1<<a)*3**(b-1)<=G):
                out.append((a,b,M))
    return out

def collect(lo,hi,K):
    pats=defaultdict(dict);seqs=[];inc=[]
    for n in range(lo|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID": continue
        if not fk.completed_rigid_source(n,K):inc.append(n);continue
        for r,seq in fk.return_sequences(n,K).items():
            if not seq:continue
            seqs.append((r,seq))
            for e in seq:
                c=e["cert"];pats[r][fk.semantic_id(c)]=c
    bank={r:tuple(pats[r][k] for k in sorted(pats[r])) for r in sorted(pats)}
    return seqs,bank,inc

def audit(lo,hi,K):
    seqs,bank,inc=collect(lo,hi,K)
    cells=defaultdict(set)
    exact=near=hi3=spacebig=0
    vmax=0; hist=defaultdict(int)
    minspace=None;maxspace=None
    for r,seq in seqs:
        cs=bank[r]
        for e in seq:
            d2,rho,b3,res3=bc.key(e,cs,"BI_CELL")
            M=(1<<d2)*3**b3
            minspace=M if minspace is None else min(minspace,M)
            maxspace=M if maxspace is None else max(maxspace,M)
            spacebig+=M>G
            cells[(d2,rho,b3,res3)].add(e["m0"])
            c=e["cert"];m0=e["m0"];m1=e["m1"];D=c["D"]
            delta=fk.defect(c,m0)
            assert (m1-m0)*(1<<D)==-delta
            exact+=1
            if delta:
                v2=v2z(delta); v3=vpz(delta,3)
                assert v2>=D+1 and v2z(m1-m0)==v2-D and vpz(m1-m0,3)==v3
                vmax=max(vmax,v3);hist[v3]+=1
                if abs(m1-m0)<=G:
                    near+=1
                    if v3>=B:
                        hi3+=1
                        assert abs(m1-m0)>=2*3**B
            else: assert m1==m0
    pairs=nonid=under=0;minq=None
    for (a,_,b,_),vals in cells.items():
        M=(1<<a)*3**b; vs=sorted(vals)
        for i,x in enumerate(vs):
            for y in vs[i+1:]:
                pairs+=1
                assert (x-y)%M==0
                if x!=y:
                    nonid+=1;q=abs(x-y)//M
                    minq=q if minq is None else min(minq,q)
                if abs(x-y)<M:
                    under+=1;assert x==y
    return {"range":[lo|1,hi],"incomplete":inc,"events":exact,"cells":len(cells),
            "same_cell_pairs":pairs,"same_cell_nonidentical":nonid,
            "same_cell_under_spacing":under,"min_nonzero_cell_quotient":minq,
            "near_return_gap_le_G":near,"near_return_active_v3_ge_20":hi3,
            "max_source_active_v3":vmax,"active_v3_hist":dict(sorted(hist.items())),
            "events_cell_spacing_gt_G":spacebig,"min_cell_spacing":minspace,"max_cell_spacing":maxspace}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    fr=threshold_frontier()
    assert (32,0,1<<32) in fr and (0,21,3**21) in fr
    bands=[audit(43009,45055,128),audit(46081,46591,128),audit(46593,47103,128)]
    result={"schema":"COLLATZ_BIADIC_SQUEEZE_V0","farey_live_gap_ceiling":G,
      "threshold_frontier":[{"a":x,"b":y,"spacing":z} for x,y,z in fr],
      "exact_return_trit_threshold":B,"exact_return_spacing":2*3**B,
      "lemma_same_cell":"same mod 2^a and 3^b plus |x-y|<2^a3^b implies x=y",
      "lemma_exact_return":"|F(m)-m|<=G and v3(Delta_F(m))>=20 implies F(m)=m",
      "bands":bands,
      "global_live_pair_same_cell_premise":"UNKNOWN_NOT_ASSUMED",
      "global_active_v3_ge_20_premise":"UNKNOWN_NOT_ASSUMED",
      "verdict":"PASS_EXACT_SQUEEZE_LEMMA_WITH_NAMED_GLOBAL_PREMISE",
      "scope":"conditional arithmetic plus bounded regression; no Collatz theorem"}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("GAP",G);print("EXACT_RETURN_THRESHOLD",B,2*3**B)
    print("FRONTIER",json.dumps(result["threshold_frontier"],sort_keys=True))
    for row in bands:print("BAND",json.dumps(row,sort_keys=True))
    print("GLOBAL_LIVE_PAIR_SAME_CELL_PREMISE",result["global_live_pair_same_cell_premise"])
    print("GLOBAL_ACTIVE_V3_GE_20_PREMISE",result["global_active_v3_ge_20_premise"])
    print("VERDICT",result["verdict"])
if __name__=="__main__":main()
