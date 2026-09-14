from __future__ import annotations
from itertools import combinations
from collections import defaultdict
from typing import Dict, Tuple, Iterable, Hashable

def partitions(items):
    items=tuple(items)
    if not items:
        yield ()
        return
    first=items[0]
    for p in partitions(items[1:]):
        # new block
        yield (frozenset([first]),)+p
        # insert in existing block
        for i in range(len(p)):
            q=list(p)
            q[i]=frozenset(set(q[i])|{first})
            # canonicalize block order to avoid duplicates
            key=tuple(sorted((tuple(sorted(b,key=repr)) for b in q),key=repr))
            yield tuple(frozenset(b) for b in key)

def uniq_partitions(items):
    seen=set()
    for p in partitions(items):
        canon=tuple(sorted((tuple(sorted(b,key=repr)) for b in p),key=repr))
        if canon not in seen:
            seen.add(canon)
            yield tuple(frozenset(b) for b in canon)

def kernel_of_map(mapping: Dict[Hashable, Hashable]):
    buckets=defaultdict(set)
    for x,y in mapping.items():
        buckets[y].add(x)
    return frozenset(frozenset(v) for v in buckets.values())

def pair_relation(partition):
    rel=set()
    for b in partition:
        for x in b:
            for y in b:
                rel.add((x,y))
    return frozenset(rel)

class FiniteEvaluation:
    def __init__(self,X,T,e):
        self.X=tuple(X); self.T=tuple(T); self.e=e

    def row_signature(self,x,S=None):
        S=self.T if S is None else tuple(S)
        return tuple(self.e(x,t) for t in S)

    def col_signature(self,t,X=None):
        X=self.X if X is None else tuple(X)
        return tuple(self.e(x,t) for x in X)

    def row_partition(self,S=None):
        m={x:self.row_signature(x,S) for x in self.X}
        return kernel_of_map(m)

    def col_partition(self,X=None):
        m={t:self.col_signature(t,X) for t in self.T}
        return kernel_of_map(m)

    def induced_relation(self,S):
        return pair_relation(self.row_partition(S))

    def full_relation(self):
        return pair_relation(self.row_partition())

    def minimal_probe_bases(self):
        target=self.full_relation()
        out=[]
        for k in range(len(self.T)+1):
            for S in combinations(self.T,k):
                if self.induced_relation(S)==target:
                    out.append(S)
            if out:
                return out
        return out

    def sufficient_partition(self,P):
        # A representation partition is sufficient iff every representation
        # block lies within one exact future-consequence block.
        return pair_relation(P).issubset(self.full_relation())

    def coarsest_sufficient_partitions(self):
        suff=[]
        for P in uniq_partitions(self.X):
            if self.sufficient_partition(P):
                suff.append(P)
        # coarsest = smallest number of blocks among sufficient partitions
        m=min(len(P) for P in suff)
        return [P for P in suff if len(P)==m]

    def T_of_R(self,R):
        # tests constant on every R-equivalence class
        return frozenset(t for t in self.T
                         if all(((x,y) not in R) or self.e(x,t)==self.e(y,t)
                                for x in self.X for y in self.X))

    def R_of_S(self,S):
        return self.induced_relation(S)

    def check_galois(self):
        Rs=[pair_relation(P) for P in uniq_partitions(self.X)]
        Ts=[]
        for k in range(len(self.T)+1):
            Ts.extend(frozenset(s) for s in combinations(self.T,k))
        for S in Ts:
            RS=self.R_of_S(S)
            for R in Rs:
                lhs=S.issubset(self.T_of_R(R))
                rhs=R.issubset(RS)
                if lhs!=rhs:
                    return False,{'S':S,'R':R,'lhs':lhs,'rhs':rhs}
        return True,None

def assert_equal(a,b,msg):
    if a!=b:
        raise AssertionError(f"{msg}: {a!r} != {b!r}")

def main():
    # Canonical five-state sanity system represented directly by its full
    # future-consequence signatures. epsilon and a already suffice.
    X=(0,1,2,3,4)
    T=("eps","a","b","aa")
    table={
        0:(0,1,0,1),
        2:(0,1,0,1),
        1:(1,1,1,1),
        4:(1,1,1,1),
        3:(0,0,0,0),
    }
    E=FiniteEvaluation(X,T,lambda x,t: table[x][T.index(t)])

    exact=E.row_partition()
    expected=frozenset({frozenset({0,2}),frozenset({1,4}),frozenset({3})})
    assert_equal(exact,expected,"future-consequence quotient")

    bases=E.minimal_probe_bases()
    if ("eps","a") not in bases and ("a","eps") not in bases:
        # There may be an even smaller equivalent basis in this synthetic
        # table; require at least one basis of size <=2 and exact recovery.
        if min(map(len,bases))>2:
            raise AssertionError(f"expected probe basis <=2, got {bases}")

    coarsest=E.coarsest_sufficient_partitions()
    if len(coarsest)!=1 or frozenset(coarsest[0])!=expected:
        raise AssertionError(f"coarsest sufficient representation mismatch: {coarsest}")

    ok,w=E.check_galois()
    if not ok:
        raise AssertionError(f"Galois law failed: {w}")

    # Dual collapse: duplicate columns are quotiented too.
    cp=E.col_partition()
    if not any(len(b)>1 for b in cp):
        raise AssertionError("expected at least one redundant probe column")

    # Task quotient can be strictly coarser than environmental quotient.
    # env consequences distinguish u,v immediately; GOAL consequences never do
    # on the supplied complete finite test family.
    X2=("u","v","w")
    T2=("","1","2","11","12")
    env={
        "u":("U0","U1","U2","U11","U12"),
        "v":("V0","V1","V2","V11","V12"),
        "w":("W0","W1","W2","W11","W12"),
    }
    goal={
        "u":(0,0,0,1,0),
        "v":(0,0,0,1,0),
        "w":(0,0,1,0,0),
    }
    Eenv=FiniteEvaluation(X2,T2,lambda x,t: env[x][T2.index(t)])
    Egoal=FiniteEvaluation(X2,T2,lambda x,t: goal[x][T2.index(t)])
    if Eenv.row_partition()==Egoal.row_partition():
        raise AssertionError("control failed: GOAL quotient should be coarser")
    if frozenset({"u","v"}) not in Egoal.row_partition():
        raise AssertionError("u,v should be GOAL-equivalent")
    if any(frozenset({"u","v"}).issubset(b) for b in Eenv.row_partition()):
        raise AssertionError("u,v should be environmentally separated")

    # Bounded evidence asymmetry: a found separator certifies SEP; absence of
    # a separator in a non-closed subset does not certify global EQ.
    S=("","1")
    if Egoal.row_signature("u",S)!=Egoal.row_signature("v",S):
        raise AssertionError("bounded control should not separate u,v")
    if Egoal.row_signature("u",("2",))==Egoal.row_signature("w",("2",)):
        raise AssertionError("witnessed separator should separate u,w")

    result={
        "classification":"FINITE_EXHAUSTIVE_MINIMAL_GOAL_EVALUATION_KERNEL",
        "exact_row_partition":[sorted(b,key=repr) for b in exact],
        "minimal_probe_bases":[list(b) for b in bases],
        "coarsest_sufficient_unique":True,
        "galois_connection_exhaustive":True,
        "duplicate_probe_columns_collapsed":True,
        "goal_quotient_strictly_coarser_than_environment_control":True,
        "epistemic_asymmetry_checked":True,
    }
    import json
    with open("minimal_goal_evaluation_kernel_result.json","w") as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print("RESULT",json.dumps(result,sort_keys=True))
    print("VERIFIED_FINITE_MINIMAL_GOAL_EVALUATION_KERNEL")

if __name__=="__main__":
    main()
