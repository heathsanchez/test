#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib, json
import collatz_switch_state_rank_probe as sr

def v2z(x):
    x=abs(x)
    if x==0:return None
    return (x & -x).bit_length()-1

def rat_v2(x):
    if x==0:return None
    return v2z(x.numerator)-v2z(x.denominator)

def centre(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])

def law_id(anchor,c):
    return (anchor,c["A"],c["B"],1<<c["D"],c["D"])

def center_id(anchor,c):
    q=centre(c); return (anchor,q.numerator,q.denominator)

def tarjan(nodes,edges):
    g=defaultdict(set)
    for a,b in edges:g[a].add(b)
    idx=0;stack=[];on=set();ind={};low={};out=[]
    def go(v):
        nonlocal idx
        ind[v]=low[v]=idx;idx+=1;stack.append(v);on.add(v)
        for w in g.get(v,()):
            if w not in ind:
                go(w);low[v]=min(low[v],low[w])
            elif w in on:low[v]=min(low[v],ind[w])
        if low[v]==ind[v]:
            cc=[]
            while True:
                w=stack.pop();on.remove(w);cc.append(w)
                if w==v:break
            out.append(cc)
    for v in nodes:
        if v not in ind:go(v)
    return [cc for cc in out if len(cc)>1 or (len(cc)==1 and cc[0] in g.get(cc[0],()))]

def collect(lo,hi,K=128):
    switches=[];zero=[];runs=[];same=0
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        for anchor,seq in sr.returns(n,K).items():
            if not seq:continue
            mstart=seq[0][1];Abar,Bbar,Pbar=1,0,1;prev=None;flags=[]
            for c,m0,m1,k0 in seq:
                q=centre(c);pulled=(Pbar*q-Bbar)/Abar
                p=rat_v2(Fraction(mstart)-pulled)
                if p is not None:
                    cur={"law":law_id(anchor,c),"center":center_id(anchor,c),"pulled":pulled,
                         "p":p,"D":c["D"],"k0":k0}
                    if prev is not None:
                        if pulled==prev["pulled"]:
                            same+=1;assert p==prev["p"]
                        else:
                            assert p>prev["p"]
                            block=(mstart>>prev["p"])&((1<<(p-prev["p"]))-1)
                            row={"source":n,"anchor":anchor,"zero":block==0,
                                 "old_law":prev["law"],"new_law":cur["law"],
                                 "old_center":prev["center"],"new_center":cur["center"],
                                 "old_D":prev["D"],"new_D":cur["D"],
                                 "old_precision":prev["p"],"new_precision":p,
                                 "depth":[prev["k0"],k0]}
                            switches.append(row);flags.append(row)
                            if row["zero"]:zero.append(row)
                    prev=cur
                else:
                    prev=None
                Abar,Bbar,Pbar=(c["A"]*Abar,c["A"]*Bbar+c["B"]*Pbar,(1<<c["D"])*Pbar)
            rr=[]
            for e in flags:
                if e["zero"]:rr.append(e)
                elif rr:runs.append(rr);rr=[]
            if rr:runs.append(rr)
    return switches,zero,runs,same

def summary(zero,runs):
    le={(e["old_law"],e["new_law"]) for e in zero}
    ln={x for e in le for x in e}
    ce={(e["old_center"],e["new_center"]) for e in zero}
    cn={x for e in ce for x in e}
    ls=tarjan(ln,le);cs=tarjan(cn,ce)
    succ=defaultdict(set)
    for a,b in le:succ[a].add(b)
    live=set(ln);layers=[];rank={};lev=0
    while live:
        dead={x for x in live if not (succ.get(x,set())&live)}
        layers.append(len(dead))
        if not dead:break
        for x in dead:rank[x]=lev
        live-=dead;lev+=1
    hist=Counter(len(x) for x in runs);longest=max(runs,key=len) if runs else []
    return {"zero_switches":len(zero),"unique_law_edges":len(le),"law_nodes":len(ln),
            "law_recurrent_sccs":len(ls),"largest_law_scc":max((len(x) for x in ls),default=0),
            "unique_center_edges":len(ce),"center_nodes":len(cn),
            "center_recurrent_sccs":len(cs),"largest_center_scc":max((len(x) for x in cs),default=0),
            "elimination_layers":layers,"leftover_nodes":len(live),"max_rank":max(rank.values(),default=None),
            "zero_run_histogram":dict(sorted(hist.items())),"max_zero_run":len(longest),
            "longest_zero_run":longest}

def main():
    ts,tz,tr,tsame=collect(3,8191)
    hs,hz,hr,hsame=collect(8193,32767)
    u=summary(tz+hz,tr+hr)
    result={"schema":"COLLATZ_ZERO_EXPOSURE_INDEPENDENT_GRAMMAR_20260930",
            "train":{"switches":len(ts),"same_center":tsame,**summary(tz,tr)},
            "heldout":{"switches":len(hs),"same_center":hsame,**summary(hz,hr)},
            "union":u,
            "verdict":"ZERO_EXPOSURE_GRAMMAR_ACYCLIC_ON_INDEPENDENT_CORPUS"
              if u["law_recurrent_sccs"]==0 and u["center_recurrent_sccs"]==0
              else "ZERO_EXPOSURE_RECURRENT_SEPARATOR",
            "global_collatz":"UNKNOWN"}
    result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True,default=str))

if __name__=="__main__":main()
