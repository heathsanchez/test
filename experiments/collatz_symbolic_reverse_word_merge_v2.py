#!/usr/bin/env python3
"""Compile exact partial reverse-word lower merges into the symbolic Collatz frontier.

Parent authority:
  collatz_symbolic_merge.py (direct descent + one inverse-odd predecessor).

New constructor:
For a binary source cylinder
    n(q)=2^k q+b,
    T^k(n(q))=3^c q+d = y(q),
take any legal reverse Complete-O prefix with o<=c odd inversions,
total shortcut cost S, and cocycle C:
    p(q)=(2^S y(q)-C)/3^o
        = 2^S 3^(c-o) q + (2^S d-C)/3^o.
If its slope is strictly below 2^k, then beyond an exact finite threshold
p(q) is positive and p(q)<n(q), while replay of the reverse word reaches y(q).
This is therefore a uniform lower-merge certificate.

The constructor strictly generalizes the parent's immediate inverse-odd merge.
Exact arithmetic only. Bounded compilation depth; no Collatz theorem.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from functools import lru_cache
from pathlib import Path

import collatz_symbolic_frontier as base
import collatz_symbolic_merge as parent


def cocycle(actions):
    S=0
    C=0
    for idx,a in enumerate(actions):
        S+=a
        C=(1<<a)*C + 3**idx
    return S,C


@lru_cache(None)
def legal_word(o:int,r:int,budget:int):
    """One legal o-inversion reverse word of total cost <=budget, if it exists."""
    if o==0:
        return ()
    if budget<o:
        return None
    mod=3**o
    r%=mod
    if r%3==0:
        return None
    tailmod=3**(o-1)
    # (2^a r -1)/3 must be integral. Mod 3 this fixes parity of a.
    start=2 if r%3==1 else 1
    for a in range(start,budget-(o-1)+1,2):
        z=(pow(2,a,mod)*r-1)%mod
        if z%3:
            continue
        rp=(z//3)%tailmod if o>1 else 0
        tail=legal_word(o-1,rp,budget-a)
        if tail is not None:
            return (a,)+tail
    return None


def max_cost_for_slope(k:int,c:int,o:int):
    """Largest S with 2^S * 3^(c-o) < 2^k."""
    S=o-1
    while S+1<=k and (1<<(S+1))*3**(c-o) < (1<<k):
        S+=1
    return S


def reverse_word_candidate(s):
    k,b,c,d=(s[x] for x in ("k","b","c","d"))
    best=None
    for o in range(1,c+1):
        budget=max_cost_for_slope(k,c,o)
        if budget<o:
            continue
        r=d%(3**o)
        w=legal_word(o,r,budget)
        if w is None:
            continue
        S,C=cocycle(w)
        den=3**o
        assert ((1<<S)*d-C)%den==0
        A=(1<<S)*3**(c-o)
        B=((1<<S)*d-C)//den
        gap=(1<<k)-A
        assert gap>0

        # Exact threshold for both positivity and strict lower merge.
        q_lower=(B-b)//gap+1
        q_positive=(-B)//A+1 if B<=0 else 0
        Q=max(0,q_lower,q_positive)
        assert A*Q+B>0
        assert A*Q+B < (1<<k)*Q+b

        row=dict(s,kind="reverse_word",o=o,actions=list(w),S=S,C=C,
                 A=A,offset=B,Q=Q)
        key=(Q,A,B,o,S,tuple(w))
        if best is None or key<best[0]:
            best=(key,row)
    return None if best is None else best[1]


def verify_reverse_word(s):
    base.verify({key:s[key] for key in ("k","b","c","d")})
    assert s["kind"]=="reverse_word"
    k,b,c,d=(s[x] for x in ("k","b","c","d"))
    o,S,C,A,B,Q=(s[x] for x in ("o","S","C","A","offset","Q"))
    w=tuple(s["actions"])
    assert len(w)==o and sum(w)==S and all(a>=1 for a in w)
    assert cocycle(w)==(S,C)
    assert 1<=o<=c

    # Uniform reverse algebra, one inverse block at a time.
    aa=3**c
    bb=d
    for a in w:
        numA=(1<<a)*aa
        numB=(1<<a)*bb-1
        assert numA%3==0 and numB%3==0
        aa=numA//3
        bb=numB//3
    assert (aa,bb)==(A,B)

    gap=(1<<k)-A
    assert gap>0
    assert Q==max(0,(B-b)//gap+1,((-B)//A+1 if B<=0 else 0))
    assert A*Q+B>0
    assert A*Q+B<(1<<k)*Q+b

    # Independent concrete replay on threshold and next parameter.
    for q in (Q,Q+1):
        n=(1<<k)*q+b
        y=3**c*q+d
        p=A*q+B
        assert 0<p<n
        x=p
        for a in reversed(w):
            assert x&1
            x=(3*x+1)//2
            for _ in range(a-1):
                assert x%2==0
                x//=2
        assert x==y
        z=n
        for _ in range(k):
            z=z//2 if z%2==0 else (3*z+1)//2
        assert z==y
    return True


def source(s):
    return {key:s[key] for key in ("k","b","c","d")}


def compile_portfolio(depth):
    base.require(1<=depth<=24,"bounded depth")
    frontier=[dict(k=0,b=0,c=0,d=0)]
    bank=[]
    exceptions=set()

    for _ in range(depth):
        pending=[]
        for s in frontier:
            k,b,c,d=(s[x] for x in ("k","b","c","d"))
            for bit in (0,1):
                r=d+bit*3**c
                child=dict(k=k+1,b=b+bit*2**k,
                           c=c+(r%2),
                           d=r//2 if r%2==0 else (3*r+1)//2)

                selected=None

                # Preserve parent ordering/meaning exactly.
                for kind in ("descent","inverse_odd"):
                    if kind=="inverse_odd" and (child["c"]==0 or child["d"]%3!=2):
                        continue
                    candidate=dict(child,kind=kind)
                    a,off=parent.reconstruction(candidate)
                    gap=2**child["k"]-a
                    if gap<=0:
                        continue
                    Q=max(0,(off-child["b"])//gap+1)
                    if a*Q+off<=0:
                        continue
                    candidate["Q"]=Q
                    parent.verify_merge(candidate)
                    selected=candidate
                    break

                if selected is None:
                    selected=reverse_word_candidate(child)
                    if selected is not None:
                        verify_reverse_word(selected)

                if selected is None:
                    pending.append(child)
                else:
                    bank.append(selected)
                    exceptions.update(
                        2**child["k"]*q+child["b"]
                        for q in range(selected["Q"])
                        if 2**child["k"]*q+child["b"]>1
                    )
        frontier=pending
    return bank,frontier,sorted(exceptions)


def verify_partition(bank,residual):
    for s in bank:
        if s["kind"]=="reverse_word":
            verify_reverse_word(s)
        else:
            parent.verify_merge(s)
    base.verify_cover([source(s) for s in bank],residual)


def applications(bank,low,high):
    result={}
    for i,s in enumerate(bank):
        mod=1<<s["k"]
        first=max(s["Q"],(low-s["b"]+mod-1)//mod)
        for n in range(mod*first+s["b"],high+1,mod):
            base.require(n not in result,"overlapping consequences")
            result[n]=i
    return result


def replay_application(n,s):
    q=n//(1<<s["k"])
    x=n
    for _ in range(s["k"]):
        x=x//2 if x%2==0 else (3*x+1)//2
    if s["kind"]=="descent":
        p=x
    elif s["kind"]=="inverse_odd":
        p=2*3**(s["c"]-1)*q+(2*s["d"]-1)//3
        assert p&1 and (3*p+1)//2==x
    else:
        p=s["A"]*q+s["offset"]
        z=p
        for a in reversed(tuple(s["actions"])):
            assert z&1
            z=(3*z+1)//2
            for _ in range(a-1):
                assert z%2==0
                z//=2
        assert z==x
    assert 0<p<n


def run(depth,output):
    bank,residual,exceptions=compile_portfolio(depth)
    verify_partition(bank,residual)

    pbank,presidual,pexceptions=parent.compile_portfolio(depth)
    parent.verify_partition(pbank,presidual)

    base.require({s["b"] for s in residual}<={s["b"] for s in presidual},
                 "new constructor enlarged residual")

    low,high=65537,131072
    admitted=applications(bank,low,high)
    prior=applications(pbank,low,high)
    base.require(set(prior)<=set(admitted),"lost parent consequence")

    for n,i in admitted.items():
        replay_application(n,bank[i])

    new=sorted(set(admitted)-set(prior))
    summary=dict(
        depth=depth,
        certificates=len(bank),
        constructors=dict(Counter(s["kind"] for s in bank)),
        parent_residual_cylinders=len(presidual),
        residual_cylinders=len(residual),
        residual_density=f"{len(residual)}/{1<<depth}",
        residual_reduction=len(presidual)-len(residual),
        parent_closed=len(prior),
        portfolio_closed=len(admitted),
        additional_closed=len(new),
        finite_exceptions=len(exceptions),
        verdict="PASS_EXACT_PARTIAL_REVERSE_WORD_LOWER_MERGE_WITH_RESIDUAL",
        scope="bounded binary-cylinder compilation; no all-depth termination or Collatz theorem",
    )

    output.mkdir(parents=True,exist_ok=True)
    for name,obj in (
        ("summary",summary),("bank",bank),("residual",residual),
        ("exceptions",exceptions),("newly_closed",new)
    ):
        (output/(name+".json")).write_text(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n")

    restored=json.loads((output/"bank.json").read_text())
    verify_partition(restored,residual)
    base.require(applications(restored,low,high)==admitted,"restart changed consequences")

    print(json.dumps(summary,indent=2,sort_keys=True))
    print("FIRST_RESIDUALS",[s["b"] for s in residual[:80]])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=18)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.depth,a.output)
