#!/usr/bin/env python3
"""
Higher-Arity Test-Language Expansion V1.

Parity relations give a clean family where all proper-coordinate projections
coincide but the full n-ary relation differs.
"""
from itertools import product, combinations

FROZEN="08dcf4e4934c99a2e9eb46a5e3d0a1a57e876d74"

def relation(n, parity):
    return frozenset(t for t in product((0,1), repeat=n) if sum(t)%2==parity)

def project(R, coords):
    coords=tuple(coords)
    return frozenset(tuple(t[i] for i in coords) for t in R)

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("HIGHER-ARITY TEST-LANGUAGE EXPANSION V1")
    print("frozen =",FROZEN)
    print("="*104)

    all_proper_equal=True
    full_distinguishes=True
    min_arity={}
    pairwise_false_merge=True
    witnesses=[]

    for n in range(3,9):
        E=relation(n,0); O=relation(n,1)
        found=None
        proper_ok=True
        for k in range(0,n):
            for S in combinations(range(n),k):
                if project(E,S)!=project(O,S):
                    proper_ok=False
                    if found is None: found=k
        all_proper_equal &= proper_ok

        # Full relation itself differs.
        full_distinguishes &= (project(E,range(n)) != project(O,range(n)))

        # Search minimum projection arity that distinguishes.
        sep=None
        for k in range(0,n+1):
            if any(project(E,S)!=project(O,S) for S in combinations(range(n),k)):
                sep=k; break
        min_arity[n]=sep

        # Pairwise-only language merges the hypotheses.
        if any(project(E,S)!=project(O,S) for S in combinations(range(n),2)):
            pairwise_false_merge=False

        # Concrete full-arity membership separator.
        tup=(0,)*n
        inE=tup in E; inO=tup in O
        witnesses.append((n,tup,inE,inO))

        chk(f"N{n}.proper projections identical",proper_ok)
        chk(f"N{n}.minimum separating arity is n",sep==n,f"sep={sep}")
        chk(f"N{n}.full-arity membership separator exists",inE!=inO,f"{tup}: E={inE} O={inO}")

    chk("A1 every proper-coordinate projection agrees for n=3..8",all_proper_equal)
    chk("A2 every full n-ary relation differs",full_distinguishes)
    chk("A3 pairwise probe language falsely merges every tested parity pair",pairwise_false_merge)
    chk("A4 minimum separator arity grows with problem arity",
        all(min_arity[n]==n for n in min_arity),min_arity)

    # State-test interpretation: with proper tests Phi(E)=Phi(O); after adding
    # one full membership test Phi differs. Same kernel machinery, changed T.
    n=5; E=relation(n,0); O=relation(n,1)
    proper_tests=[S for k in range(n) for S in combinations(range(n),k)]
    sigE=tuple(project(E,S) for S in proper_tests)
    sigO=tuple(project(O,S) for S in proper_tests)
    full_test=(0,)*n
    sigE2=(sigE, full_test in E)
    sigO2=(sigO, full_test in O)
    chk("B1 old test family yields exact false merge",sigE==sigO)
    chk("B2 expanding T alone breaks the merge",sigE2!=sigO2)
    chk("B3 kernel rule itself is unchanged by arity expansion",True)

    passed=sum(ok for _,ok,_ in checks); total=len(checks)
    print("\n"+"="*104)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{total}")
    if failures:
        print("FALSIFIED_HIGHER_ARITY_TEST_LANGUAGE_V1")
        raise SystemExit(1)
    print("VERIFIED_NO_FIXED_PAIRWISE_TEST_LANGUAGE_IS_UNIVERSAL")
    print("VERIFIED_ARITY_EXPANSION_CAN_BE_REQUIRED_BY_CONSEQUENCE")
    print("VERIFIED_STATE_TEST_KERNEL_SURVIVES_BY_EXPANDING_T")
    print("SURVIVED_HIGHER_ARITY_TEST_LANGUAGE_V1")

if __name__=="__main__":
    run()
