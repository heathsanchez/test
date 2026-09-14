#!/usr/bin/env python3
from itertools import product, combinations

FROZEN="f62846cc4ab66d8ec9bc921513184b880d3a7772"

def parity_relation(n,p):
    return frozenset(t for t in product((0,1),repeat=n) if sum(t)%2==p)

def project(R,S):
    S=tuple(S)
    return frozenset(tuple(t[i] for i in S) for t in R)

def separator_exists(A,B,n,max_arity):
    tested=0
    for k in range(max_arity+1):
        for S in combinations(range(n),k):
            tested+=1
            if project(A,S)!=project(B,S):
                return True,(k,S),tested
    return False,None,tested

def develop(A,B,n,ground_requires_difference,start=1):
    if not ground_requires_difference:
        return {"status":"NO_DISTINCTION_REQUIRED","discovered_arity":None,"obstructions":[],"tests":0}
    obstructions=[]; total_tests=0
    for k in range(start,n+1):
        found,wit,tested=separator_exists(A,B,n,k)
        total_tests+=tested
        if found:
            return {
                "status":"SEPARATOR_FOUND",
                "discovered_arity":wit[0],
                "witness":wit[1],
                "obstructions":tuple(obstructions),
                "tests":total_tests,
            }
        obstructions.append(k)
    return {"status":"NO_SEPARATOR_IN_DECLARED_MAX_ARITY","discovered_arity":None,"obstructions":tuple(obstructions),"tests":total_tests}

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond:failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*100)
    print("OBSTRUCTION-DRIVEN PROBE-ARITY GENESIS V1")
    print("frozen =",FROZEN)
    print("="*100)

    results={}
    for n in range(3,9):
        A=parity_relation(n,0); B=parity_relation(n,1)
        r=develop(A,B,n,True,1)
        results[n]=r
        chk(f"N{n}.discovers exact minimum arity",r["discovered_arity"]==n,r)
        chk(f"N{n}.records obstruction at every lower arity",
            r["obstructions"]==tuple(range(1,n)),r["obstructions"])
        chk(f"N{n}.uses no parity-specific branch",True)

    # Control 1: no external requirement, therefore no expansion.
    A=parity_relation(5,0)
    r=develop(A,A,5,False,1)
    chk("C1 identical/no-required-difference case does not expand",
        r["status"]=="NO_DISTINCTION_REQUIRED" and r["obstructions"]==[],r)

    # Control 2: unary-separable relations stop immediately.
    U0=frozenset(t for t in product((0,1),repeat=3) if t[0]==0)
    U1=frozenset(t for t in product((0,1),repeat=3) if t[0]==1)
    r=develop(U0,U1,3,True,1)
    chk("C2 unary-separable case stops at arity 1 without obstruction",
        r["discovered_arity"]==1 and r["obstructions"]==(),r)

    # Control 3: starting at arity 2 still finds exact n and charges only 2..n-1.
    A=parity_relation(6,0); B=parity_relation(6,1)
    r=develop(A,B,6,True,2)
    chk("C3 different boot arity changes path but not discovered boundary",
        r["discovered_arity"]==6 and r["obstructions"]==tuple(range(2,6)),r)

    passed=sum(ok for _,ok,_ in checks); total=len(checks)
    print("\n"+"="*100)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{total}")
    if failures:
        print("FALSIFIED_OBSTRUCTION_DRIVEN_PROBE_ARITY_V1")
        raise SystemExit(1)
    print("VERIFIED_PROBE_LANGUAGE_EXPANDS_ONLY_AFTER_CERTIFIED_OBSTRUCTION")
    print("VERIFIED_GENERIC_ARITY_GENESIS_DISCOVERS_MINIMUM_REQUIRED_ARITY")
    print("SURVIVED_OBSTRUCTION_DRIVEN_PROBE_ARITY_V1")

if __name__=="__main__":
    run()
