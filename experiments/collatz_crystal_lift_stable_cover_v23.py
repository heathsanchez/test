#!/usr/bin/env python3
"""Crystal V23: lift-stable constructor cylinders and exact source-class cover.

Input is the frozen V22 certificate ledger over odd sources <2^20.
No larger source census is used.

Each concrete constructor is promoted only when its affine certificate is
stable under an infinite arithmetic progression of source lifts.

Direct:
    T^a(n)=(3^q n+B)/2^a < n.
If 3^q<2^a, the same parity prefix gives descent for every
n' = n + 2^a t.

Quarter splice:
For n' = n + 2^(a+3)t the endpoint changes by 8*3^q t, so x mod 8 is
unchanged.  If 3^q <= 4*2^a, x<=4n remains true for every lift.

Lower-source merge:
If T^a(n)=T^b(p), qn/qp are the odd counts, set
    c=(qp-qn)_+, d=(qn-qp)_+
    Mn=2^a 3^c, Mp=2^b 3^d.
For every t,
    n'=n+Mn*t, p'=p+Mp*t
follow the same two parity prefixes and meet at the same shifted common
future.  If Mp<=Mn, p'<n' persists for every t.

Thus every admitted certificate becomes an exact cylinder
    n == r2 mod 2^A, n == r3 mod 3^C.
The final DFS asks whether these finitely many universal cylinders cover all
four source classes already forced for a hypothetical minimal bad source:
n mod 24 in {3,7,15,19}.

A complete cover would still require the generic lifting lemmas to be checked
in Lean before Collatz promotion.  An uncovered cell is an exact symbolic
counterfactual residual, not a Collatz counterexample.
"""
from __future__ import annotations
import csv, json, sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

def read_rows(path):
    with open(path,newline="") as f:
        yield from csv.DictReader(f,delimiter="\t")

def stable_cylinders(path):
    counts=Counter()
    cyl={}
    unstable=[]
    for row in read_rows(path):
        n=int(row["n"]); kind=row["kind"]; a=int(row["a"]); q=int(row["qn"])
        p=int(row["p"]); b=int(row["b"]); qp=int(row["qp"]); x=int(row["x"])
        counts["raw_"+kind]+=1
        if kind=="D":
            if pow(3,q) < (1<<a):
                A,C=a,0
                key=(A,C,n%(1<<A),0)
                cyl.setdefault(key,{"kind":"D","n":n,"a":a,"q":q,"x":x})
                counts["stable_D"]+=1
            else:
                counts["unstable_D"]+=1
        elif kind=="S":
            if pow(3,q) <= 4*(1<<a):
                A,C=a+3,0
                key=(A,C,n%(1<<A),0)
                cyl.setdefault(key,{"kind":"S","n":n,"a":a,"q":q,"x":x})
                counts["stable_S"]+=1
            else:
                counts["unstable_S"]+=1
        elif kind=="M":
            c=max(qp-q,0); d=max(q-qp,0)
            Mn=(1<<a)*pow(3,c)
            Mp=(1<<b)*pow(3,d)
            if Mp<=Mn:
                A,C=a,c
                r2=n%(1<<A) if A else 0
                r3=n%pow(3,C) if C else 0
                key=(A,C,r2,r3)
                cyl.setdefault(key,{"kind":"M","n":n,"p":p,"a":a,"b":b,
                                    "q":q,"qp":qp,"x":x,
                                    "Mn":str(Mn),"Mp":str(Mp)})
                counts["stable_M"]+=1
            else:
                counts["unstable_M"]+=1
                if len(unstable)<30:
                    unstable.append({"n":n,"p":p,"a":a,"b":b,"q":q,"qp":qp,
                                     "Mn_bits":Mn.bit_length(),"Mp_bits":Mp.bit_length()})
        elif kind=="R":
            counts["raw_R"]+=1
    return counts,cyl,unstable

def compatible(cell,c):
    a,r2,b,r3=cell
    A,C,R2,R3=c
    m2=min(a,A)
    if m2 and (r2 & ((1<<m2)-1)) != (R2 & ((1<<m2)-1)):
        return False
    m3=min(b,C)
    if m3:
        mod=pow(3,m3)
        if r3%mod != R3%mod:
            return False
    return True

def covers(cell,c):
    a,r2,b,r3=cell
    A,C,R2,R3=c
    if A>a or C>b:return False
    if A and r2%(1<<A)!=R2:return False
    if C and r3%pow(3,C)!=R3:return False
    return True

def exact_cover_search(cyl):
    keys=list(cyl)
    domain=[
        (3,3,1,0), # n mod 8=3, mod3=0
        (3,3,1,1),
        (3,7,1,0),
        (3,7,1,1),
    ]
    stats=Counter()
    max_depth=0

    sys.setrecursionlimit(100000)

    def dfs(cell, candidates, depth=0):
        nonlocal max_depth
        max_depth=max(max_depth,depth)
        stats["cells"]+=1
        # Any compatible cylinder already no more specific than this cell
        # covers the whole cell.
        for c in candidates:
            if covers(cell,c):
                stats["covered_cells"]+=1
                return None

        # Retain only cylinders that can cover some descendant.
        cand=[c for c in candidates if compatible(cell,c)]
        if not cand:
            stats["uncovered_cells"]+=1
            return {"cell":cell,"reason":"NO_COMPATIBLE_CYLINDER"}

        a,r2,b,r3=cell
        need2=sum(1 for A,C,R2,R3 in cand if A>a)
        need3=sum(1 for A,C,R2,R3 in cand if C>b)
        if need2==0 and need3==0:
            # Then one should have covered above.
            stats["logic_gap"]+=1
            return {"cell":cell,"reason":"COMPATIBLE_BUT_NO_DEEPER_REQUIREMENT"}

        # Binary split has two children; prefer it unless substantially fewer
        # candidates actually require binary refinement.
        if need2 and (not need3 or 2*need2 >= need3):
            bit=1<<a
            for d in (0,1):
                ch=(a+1,r2+d*bit,b,r3)
                sub=[c for c in cand if compatible(ch,c)]
                bad=dfs(ch,sub,depth+1)
                if bad is not None:return bad
        else:
            unit=pow(3,b)
            for d in (0,1,2):
                ch=(a,r2,b+1,r3+d*unit)
                sub=[c for c in cand if compatible(ch,c)]
                bad=dfs(ch,sub,depth+1)
                if bad is not None:return bad
        return None

    for cell in domain:
        cand=[c for c in keys if compatible(cell,c)]
        bad=dfs(cell,cand)
        if bad is not None:
            bad["domain_start"]=cell
            return False,bad,stats,max_depth
    return True,None,stats,max_depth

def main():
    if len(sys.argv)!=3:
        raise SystemExit("usage: v23.py certs.tsv result.json")
    counts,cyl,unstable=stable_cylinders(sys.argv[1])
    bykind=Counter(v["kind"] for v in cyl.values())
    expairs=Counter((k[0],k[1]) for k in cyl)
    complete,bad,stats,maxdepth=exact_cover_search(cyl)

    result={
      "schema":"COLLATZ_CRYSTAL_LIFT_STABLE_COVER_V23",
      "training_boundary":"odd sources 3<=n<2^20 from frozen V22 ledger",
      "larger_source_census":False,
      "certificate_counts":dict(sorted(counts.items())),
      "unique_stable_cylinders":len(cyl),
      "stable_cylinders_by_kind":dict(sorted(bykind.items())),
      "distinct_exponent_pairs":len(expairs),
      "max_binary_exponent":max((a for a,c,r2,r3 in cyl),default=0),
      "max_ternary_exponent":max((c for a,c,r2,r3 in cyl),default=0),
      "unstable_merge_examples":unstable,
      "universal_source_class_cover":complete,
      "first_uncovered_symbolic_cell":bad,
      "cover_search_stats":dict(sorted(stats.items())),
      "cover_search_max_depth":maxdepth,
      "interpretation":(
        "Every retained cylinder is algebraically lift-stable. Cover completeness "
        "is an exact finite congruence question over the four minimal-bad source "
        "classes; incompleteness emits a counterfactual residue cell rather than "
        "using resolved-source trajectories."
      ),
      "promotion_boundary":(
        "Even if the congruence cover is complete, generic direct/splice/merge "
        "lifting and the finite cover must be independently checked in Lean "
        "before any Collatz theorem is claimed."
      ),
      "global_collatz":"UNKNOWN"
    }
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
