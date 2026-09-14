#!/usr/bin/env python3
"""Ground–Preference Separation V1."""

FROZEN="7d14e7668c30288b97aa088b30f0a2b5cc6efe2e"

def scalar_score(M,violations,cost):
    return M*violations+cost

def lex_key(violations,cost):
    return (violations,cost)

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*100)
    print("GROUND–PREFERENCE SEPARATION V1")
    print("frozen =",FROZEN)
    print("="*100)

    # Exhaust a range of finite penalties and construct the adversary guaranteed
    # by the theorem: invalid cost 0 vs valid cost M+1.
    penalties=[0,1,2,5,10,100,10**3,10**6]
    for M in penalties:
        invalid=(1,0)
        valid=(0,M+1)
        scalar_prefers_invalid=scalar_score(M,*invalid) < scalar_score(M,*valid)
        lex_prefers_valid=lex_key(*valid) < lex_key(*invalid)
        chk(f"M={M}: finite scalar penalty can prefer invalid candidate",
            scalar_prefers_invalid,
            f"invalid={scalar_score(M,*invalid)} valid={scalar_score(M,*valid)}")
        chk(f"M={M}: lexicographic ground always prefers valid candidate",
            lex_prefers_valid)

    # Symbolic family check for arbitrary nonnegative integer M up to a broad bound.
    universal_witness=True
    for M in range(10001):
        if not (scalar_score(M,1,0) < scalar_score(M,0,M+1)):
            universal_witness=False; break
    chk("A1 adversarial family defeats every finite integer penalty M<=10000",universal_witness)

    # Within lawful candidates, cost is free to order.
    lawful=[("slow",0,10),("fast",0,3),("mid",0,6)]
    scalar_choice=min(lawful,key=lambda x:scalar_score(1,x[1],x[2]))[0]
    lex_choice=min(lawful,key=lambda x:lex_key(x[1],x[2]))[0]
    chk("A2 within the lawful set ordinary cost selects the cheaper realization",
        scalar_choice=="fast" and lex_choice=="fast",
        f"scalar={scalar_choice} lex={lex_choice}")

    # Bounded-domain control: if an explicit cost bound B is warranted, a finite
    # penalty larger than B CAN simulate lexicographic validity on that bounded scope.
    B=100; M=B+1
    bounded_ok=True
    for vcost in range(B+1):
        for icost in range(B+1):
            valid=(0,vcost); invalid=(1,icost)
            if not (scalar_score(M,*valid) < scalar_score(M,*invalid)):
                bounded_ok=False
    chk("A3 bounded-scope exception is real: M>B enforces validity for costs<=B",bounded_ok)

    passed=sum(ok for _,ok,_ in checks); total=len(checks)
    print("\n"+"="*100)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{total}")
    if failures:
        print("FALSIFIED_GROUND_PREFERENCE_SEPARATION_V1")
        raise SystemExit(1)
    print("VERIFIED_NO_FIXED_FINITE_SCALAR_PENALTY_IS_UNIVERSALLY_CORRECTNESS_FIRST")
    print("VERIFIED_HARD_OR_LEXICOGRAPHIC_GROUND_LAYER")
    print("VERIFIED_BOUNDED_SCOPE_CAN_ADMIT_FINITE_SCALARIZATION")
    print("SURVIVED_GROUND_PREFERENCE_SEPARATION_V1")

if __name__=="__main__":
    run()
