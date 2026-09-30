#!/usr/bin/env python3
"""Crystal discovery: smallest exact rank law for consecutive zero-block switches.

A zero-block switch is a genuine centre switch whose newly resolved pulled-source
bit block is all zero. An ordinary natural source with infinitely many switches
would eventually have only such switches. The previous bounded tournament found
the zero-block switch subgraph acyclic. This script extracts its elimination rank
and asks what exact return-law coordinates determine/decrease that rank.

Discovery only. Any surviving law must be frozen and challenged prospectively.
"""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict,Counter
from contextlib import redirect_stdout
from fractions import Fraction
from itertools import combinations,product
import io
with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra

def v2z(x):
    x=abs(int(x))
    if x==0:return None
    return (x&-x).bit_length()-1
def rv2(x): return v2z(x.numerator)-v2z(x.denominator)
def ctr(c): return Fraction(c["B"],(1<<c["D"])-c["A"])
def sid(c): return (c["r"],c["A"],c["B"],c["D"])
def log3pow(A):
    q=0;x=A
    while x%3==0 and x>1:x//=3;q+=1
    assert x==1
    return q
def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            st=last[r];w=tuple(branches[st:end])
            c=cache.setdefault(w,ra.certificate(w))
            m0=starts[st][2];m1=starts[end][2]
            assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
            out[r].append((c,m0,m1))
        last[r]=end
    return out
def collect(lo,hi,K):
    seqs=[]
    start=max(3,lo)+(max(3,lo)%2==0)
    for n in range(start,hi+1,2):
      for anchor,seq in returns(n,K).items():
        if len(seq)<2:continue
        owner=seq[0][1];Abar=Pbar=1;Bbar=0;st=[]
        for c,m0,m1 in seq:
            pc=(Pbar*ctr(c)-Bbar)/Abar
            p=rv2(Fraction(owner)-pc);assert p is not None
            st.append((c,pc,p))
            Abar,Bbar,Pbar=(c["A"]*Abar,c["A"]*Bbar+c["B"]*Pbar,(1<<c["D"])*Pbar)
        sw=[]
        for a,b in zip(st,st[1:]):
            ca,pa,p0=a;cb,pb,p1=b
            if pa==pb:continue
            assert p1>p0
            block=(owner>>p0)&((1<<(p1-p0))-1)
            sw.append({"old":sid(ca),"new":sid(cb),"zero":block==0,
                       "p0":p0,"p1":p1,"source":n,"anchor":anchor})
        if sw:seqs.append(sw)
    return seqs
def elim_rank(nodes,succ):
    live=set(nodes);rank={};layer=0;layers=[]
    while live:
        dead={n for n in live if not (succ[n]&live)}
        if not dead:return rank,live,layers
        layers.append(len(dead))
        for n in dead:rank[n]=layer
        live-=dead;layer+=1
    return rank,set(),layers
def node_features(node):
    o,n=node
    ro,Ao,Bo,Do=o;rn,An,Bn,Dn=n
    qo=log3pow(Ao);qn=log3pow(An)
    Co=(1<<Do)-Ao;Cn=(1<<Dn)-An
    G=Co*Bn-Cn*Bo
    h=None if G==0 else v2z(G)
    return {
      "old_r":ro,"new_r":rn,
      "old_D":Do,"new_D":Dn,"D_delta":Dn-Do,
      "old_q":qo,"new_q":qn,"q_delta":qn-qo,
      "old_B_bits":abs(Bo).bit_length(),"new_B_bits":abs(Bn).bit_length(),
      "old_C_bits":abs(Co).bit_length(),"new_C_bits":abs(Cn).bit_length(),
      "gap_v2":-1 if h is None else h,
      "old_D_minus_q":Do-qo,"new_D_minus_q":Dn-qn,
    }
def audit(lo,hi,K):
    seqs=collect(lo,hi,K)
    nodes=set();succ=defaultdict(set);edges=set();occ=0
    for sw in seqs:
        for a,b in zip(sw,sw[1:]):
            if a["zero"] and b["zero"]:
                u=(a["old"],a["new"]);v=(b["old"],b["new"])
                nodes|={u,v};succ[u].add(v);succ.setdefault(v,set());edges.add((u,v));occ+=1
    for n in nodes:succ.setdefault(n,set())
    rank,left,layers=elim_rank(nodes,succ)
    assert not left
    F={n:node_features(n) for n in nodes}
    fields=list(next(iter(F.values())).keys()) if F else []
    scalar={}
    for k in fields:
        ds=[F[u][k]-F[v][k] for u,v in edges]
        scalar[k]={
          "strict_down":bool(ds) and all(d>0 for d in ds),
          "nonincrease":bool(ds) and all(d>=0 for d in ds),
          "strict_up":bool(ds) and all(d<0 for d in ds),
          "nondecrease":bool(ds) and all(d<=0 for d in ds),
          "min":min(ds) if ds else None,"max":max(ds) if ds else None,
        }
    lex=[]
    for a,b in combinations(fields,2):
      for sa,sb in product((1,-1),repeat=2):
        if edges and all((sa*F[v][a],sb*F[v][b]) < (sa*F[u][a],sb*F[u][b]) for u,v in edges):
            lex.append({"features":[a,b],"signs":[sa,sb]})
    functional=[]
    for sz in range(1,min(5,len(fields))+1):
      for sub in combinations(fields,sz):
        g={};bad=False
        for n in nodes:
            key=tuple(F[n][x] for x in sub);r=rank[n]
            if key in g and g[key]!=r:bad=True;break
            g[key]=r
        if not bad:functional.append({"fields":sub,"classes":len(g)})
      if functional:break
    drop=Counter(rank[u]-rank[v] for u,v in edges)
    return {
      "range":[lo,hi],"sequences":len(seqs),"nodes":len(nodes),"edges":len(edges),
      "edge_occurrences":occ,"layers":layers,"max_rank":max(rank.values(),default=-1),
      "rank_drop_histogram":dict(sorted(drop.items())),
      "scalar":scalar,"lex":lex[:50],"minimum_rank_functional_subsets":functional[:50],
      "sample_rank4":[{"node":n,"features":F[n]} for n in nodes if rank.get(n)==max(rank.values(),default=-1)][:10],
    }
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--K",type=int,default=128);a=ap.parse_args()
    d=audit(3,32767,a.K)
    tiny=[k for k,v in d["scalar"].items() if v["strict_down"]]
    verdict=("ZERO_BLOCK_SIMPLE_RANK_FOUND" if tiny or d["lex"] else
             "ZERO_BLOCK_RANK_REQUIRES_RICH_SWITCH_IDENTITY")
    print(json.dumps({"schema":"COLLATZ_ZERO_BLOCK_RANK_CRYSTAL_20260930",
      "discovery":d,"strict_scalar_candidates":tiny,"verdict":verdict,
      "global_collatz":"UNKNOWN"},indent=2,default=list))
if __name__=="__main__":main()
