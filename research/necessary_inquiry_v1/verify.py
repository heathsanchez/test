#!/usr/bin/env python3
"""Exact bounded necessity-driven inquiry verifier. No physical/unbounded claim.
Model f(x)=c xor <a,x> xor sum_(i,j in E) x_i*x_j (mod 2), |E|<=2.
Source-independent probes, exhaustive 2-sparse syndrome uniqueness, replay.
Strong stateless sparse control using the same probes has identical cost.
"""
from itertools import combinations
from random import Random
import json

def edges(n):
    return tuple(combinations(range(n),2))

def design(n):
    rng=Random(1337+n)
    ee=edges(n)
    masks=[]
    for _ in range(128):
        a=b=0
        for i in range(n):
            v=rng.randrange(3)
            if v==1:a|=1<<i
            elif v==2:b|=1<<i
        if not a or not b:continue
        masks.append((a,b))
        if len(masks)<32 or len(masks)%8:continue
        columns=[]
        for i,j in ee:
            s=0
            for k,(a,b) in enumerate(masks):
                if ((a>>i&1) and (b>>j&1)) or ((a>>j&1) and (b>>i&1)):
                    s|=1<<k
            columns.append(s)
        # Exact complete sparse-decoding certificate, independent of targets.
        seen={0}
        good=True
        for x in columns:
            if x in seen:good=False;break
            seen.add(x)
        if not good:continue
        for i,x in enumerate(columns):
            for y in columns[i+1:]:
                t=x^y
                if t in seen:good=False;break
                seen.add(t)
            if not good:break
        if good:
            assert len(seen)==1+len(ee)+len(ee)*(len(ee)-1)//2
            # Independently check every probe annihilates affine basis.
            for a,b in masks:
                assert not a&b
                assert all(sum((v>>i)&1 for v in (0,a,b,a|b))%2==0
                           for i in range(n))
            return masks,columns
    raise AssertionError(("no qualified design",n))

class Oracle:
    def __init__(self,n,c,a,ee):
        self.n,self.c,self.a,self.ee=n,c,a,ee
        self.cache={}
    def get(self,x):
        if x not in self.cache:
            self.cache[x]=self.c^((self.a&x).bit_count()%2)^(
                sum(((x>>i)&1)*((x>>j)&1) for i,j in self.ee)%2)
        return self.cache[x]

def decode(n,o,masks,columns):
    z=o.get(0)
    s=0
    for k,(a,b) in enumerate(masks):
        s|=(o.get(a)^o.get(b)^o.get(a|b)^z)<<k
    one={x:i for i,x in enumerate(columns)}
    if s==0:idx=()
    elif s in one:idx=(one[s],)
    else:
        idx=None
        for i,x in enumerate(columns):
            j=one.get(s^x)
            if j is not None and i<j:
                idx=(i,j);break
    if idx is None:return None
    a=sum((o.get(1<<i)^z)<<i for i in range(n))
    return z,a,tuple(edges(n)[i] for i in idx)

def full(n,o):
    z=o.get(0)
    aa=[o.get(1<<i)^z for i in range(n)]
    a=sum(v<<i for i,v in enumerate(aa))
    ee=tuple((i,j) for i,j in edges(n)
             if o.get((1<<i)|(1<<j))^z^aa[i]^aa[j])
    return z,a,ee

def truth(x,n,c,a,ee):
    y=c
    for i in range(n):
        if x&(1<<i) and a&(1<<i):y^=1
    for i,j in ee:
        if x&(1<<i) and x&(1<<j):y^=1
    return y

def task(n,k,seed):
    rng=Random(seed)
    return n,rng.randrange(2),rng.getrandbits(n),tuple(sorted(rng.sample(edges(n),k)))

def check_cycle():
    n=5;ee=edges(n);cycle=None
    for r in range(1,4):
        for group in combinations(ee,r):
            if all(sum(v in edge for edge in group)%2==0 for v in range(n)):
                cycle=group;break
        if cycle is not None:break
    assert cycle is not None and len(cycle)==3
    def f(x):return sum((x>>i&1)*(x>>j&1) for i,j in cycle)%2
    assert all(f(s)^f(31^s)^f(31)^f(0)==0 for s in range(32))
    witness=None
    for q in (2,4):
        for seq in combinations(range(32),q):
            if any(sum((x>>i)&1 for x in seq)%2 for i in range(5)):continue
            if sum(f(x) for x in seq)%2:
                witness=seq;break
        if witness is not None:break
    assert witness and len(witness)==4
    return {"kernel_edges":cycle,"four_query_separator":witness}

def main():
    summary=[]
    all_designs={}
    for n in (8,16,32,64):
        masks,columns=design(n)
        all_designs[n]=(masks,columns)
        good=old=0
        nq=fq=pq=0
        for k in (0,1,2):
            for t in range(2 if n==8 else 6):
                seed=(100000 if n==8 else 700000)+n*1000+k*100+t
                nn,c,a,ee=task(n,k,seed)
                o=Oracle(nn,c,a,ee)
                d=decode(n,o,masks,columns)
                assert d==(c,a,ee),(n,seed,d,ee)
                nq+=len(o.cache)
                b=Oracle(nn,c,a,ee)
                assert full(n,b)==d
                fq+=len(b.cache)
                choose_sparse=(1+n+3*len(masks))<1+n+len(edges(n))
                p=Oracle(nn,c,a,ee)
                assert (decode(n,p,masks,columns) if choose_sparse else full(n,p))==d
                pq+=len(p.cache)
                # Separate interpretation: do not rely on learner evaluation.
                rng=Random(seed+1234)
                inputs=range(1<<n) if n==8 else (rng.getrandbits(n) for _ in range(512))
                assert all(truth(x,n,*d)==truth(x,n,c,a,ee) for x in inputs)
                good+=1
                old+=(k==0)
        summary.append({"n":n,"tasks":good,"affine_only_successes":old,
                        "qualified_probe_tests":len(masks),
                        "sparse_queries":nq//good,"full_queries":fq//good,
                        "portfolio_queries":pq//good,
                        "portfolio_method":"sparse" if choose_sparse else "full"})
        for ee in (((0,1),(0,2),(1,2)),((0,1),(2,3),(4,5))):
            assert decode(n,Oracle(n,1,0,ee),masks,columns) is None
    assert [(v["sparse_queries"],v["full_queries"],v["portfolio_queries"])
            for v in summary]==[(82,37,37),(113,137,113),(153,529,153),(233,2081,233)]
    cycle=check_cycle()
    o=Oracle(8,1,17,((0,1),(2,3)))
    assert decode(8,o,*all_designs[8]) is not None
    unobserved=next(i for i in range(256) if i not in o.cache)
    assert all(o.cache[x]==o.cache[x]^(int(x==unobserved)) for x in o.cache)
    print(json.dumps({"status":"PASS_EXACT_BOUNDED","summary":summary,
                      "cut_cycle_no_go":cycle,"outside_grammar_alias_input":unobserved,
                      "strong_identical_sparse_comparator":"TIE_BY_CONSTRUCTION"},indent=2))

if __name__=="__main__":
    main()
