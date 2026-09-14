#!/usr/bin/env python3
"""
Consequential Information Factorization V1 — exhaustive finite tests.

Part A: all deterministic maps X={0,1,2,3}->R={0,1,2,3}.
Part B: all binary-input/binary-output stochastic channels with row
probabilities on the exact grid {0,1/4,1/2,3/4,1}.
"""
from fractions import Fraction as F
from itertools import product

FROZEN="1c0b4f2acf54fef98c1ce6508bc8fff0b328ecf6"

# ---------- deterministic maps ----------

X=tuple(range(4))
LABELS=tuple(range(4))
DMAPS=tuple(product(LABELS, repeat=len(X)))  # 256

def d_kernel(r):
    return frozenset((x,y) for x in X for y in X if r[x]==r[y])

def d_factors(r1,r2):
    """r1 >= r2 iff r2=f∘r1 for some deterministic f."""
    mapping={}
    for x in X:
        a=r1[x]; b=r2[x]
        if a in mapping and mapping[a]!=b:
            return False
        mapping[a]=b
    return True

# ---------- binary stochastic channels ----------

GRID=(F(0),F(1,4),F(1,2),F(3,4),F(1))
CHANNELS=tuple((p0,p1) for p0 in GRID for p1 in GRID)

def s_kernel(ch):
    return "MERGED" if ch[0]==ch[1] else "DISCRETE"

def dominates(a,b):
    """a >= b iff b is a stochastic post-processing/garbling of a."""
    p0,p1=a; q0,q1=b
    if p0==p1:
        # no state information survives a; post-processing stays state-independent.
        return q0==q1
    d=(q1-q0)/(p1-p0)
    u=q0-d*p0
    v=u+d
    return F(0)<=u<=F(1) and F(0)<=v<=F(1)

def strict_dom(a,b):
    return dominates(a,b) and not dominates(b,a)

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("CONSEQUENTIAL INFORMATION FACTORIZATION V1")
    print("frozen =",FROZEN)
    print("="*104)

    print("\n--- A. DETERMINISTIC REDUCTION ---")
    pairs=0
    agrees=True
    mutual_same_kernel=True
    same_kernel_mutual=True
    for r1 in DMAPS:
        k1=d_kernel(r1)
        for r2 in DMAPS:
            pairs+=1
            k2=d_kernel(r2)
            fac=d_factors(r1,r2)
            ref=(k1<=k2)
            if fac!=ref:
                agrees=False
            mutual=fac and d_factors(r2,r1)
            if mutual and k1!=k2:
                mutual_same_kernel=False
            if k1==k2 and not mutual:
                same_kernel_mutual=False
    chk("A1 enumerated all 65,536 ordered deterministic representation pairs",pairs==65536,pairs)
    chk("A2 deterministic factorization iff kernel refinement",agrees)
    chk("A3 deterministic mutual factorization implies equal kernels",mutual_same_kernel)
    chk("A4 equal deterministic kernels imply mutual factorization up to relabeling",same_kernel_mutual)

    print("\n--- B. STOCHASTIC INFORMATION PREORDER ---")
    npairs=0
    reflexive=True
    transitive=True
    mutual_preserves_kernel=True
    same_kernel_oneway=[]
    strict_pairs=0
    mutual_pairs=0

    for a in CHANNELS:
        reflexive &= dominates(a,a)
        for b in CHANNELS:
            npairs+=1
            ab=dominates(a,b); ba=dominates(b,a)
            if ab and ba:
                mutual_pairs+=1
                if s_kernel(a)!=s_kernel(b):
                    mutual_preserves_kernel=False
            if ab and not ba:
                strict_pairs+=1
                if s_kernel(a)==s_kernel(b):
                    same_kernel_oneway.append((a,b))
            if ab:
                for c in CHANNELS:
                    if dominates(b,c) and not dominates(a,c):
                        transitive=False

    chk("B1 enumerated all 625 ordered stochastic channel pairs",npairs==625,npairs)
    chk("B2 factorization preorder is reflexive on the full grid",reflexive)
    chk("B3 factorization preorder is transitive on the full grid",transitive)
    chk("B4 mutual stochastic factorization preserves exact kernel",mutual_preserves_kernel,
        f"mutual_pairs={mutual_pairs}")
    chk("B5 same exact kernel can still have strict information order",
        len(same_kernel_oneway)>0,
        f"oneway_same_kernel={len(same_kernel_oneway)} first={same_kernel_oneway[:1]}")
    chk("B6 strict information comparisons occur",strict_pairs>0,strict_pairs)

    perfect=(F(0),F(1))
    noisy=(F(1,4),F(3,4))
    constant=(F(1,2),F(1,2))
    chk("B7 explicit strict chain perfect > noisy > constant",
        strict_dom(perfect,noisy) and strict_dom(noisy,constant),
        f"{perfect}>{noisy}>{constant}")
    chk("B8 perfect and noisy have identical exact kernels",
        s_kernel(perfect)==s_kernel(noisy)=="DISCRETE")

    print("\n--- C. SUFFICIENCY / MINIMALITY ---")
    min_correct=True
    tested=0
    for phi in CHANNELS:
        sufficient=[r for r in CHANNELS if dominates(r,phi)]
        minima=[]
        for r in sufficient:
            # r is minimal in information among sufficient candidates if no q is
            # strictly below r while still sufficient.
            has_strict_lower=False
            for q in sufficient:
                if dominates(r,q) and not dominates(q,r):
                    has_strict_lower=True
                    break
            if not has_strict_lower:
                minima.append(r)
        expected=[r for r in CHANNELS if dominates(r,phi) and dominates(phi,r)]
        if set(minima)!=set(expected):
            min_correct=False
        tested+=1
    chk("C1 tested minimal sufficient class for all 25 consequence channels",tested==25,tested)
    chk("C2 minimal sufficient channels are exactly mutual-factorization class of Phi",min_correct)

    n=sum(ok for _,ok,_ in checks); total=len(checks)
    print("\n"+"="*104)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {n}/{total}")
    if failures:
        print("FALSIFIED_CONSEQUENTIAL_INFORMATION_FACTORIZATION_V1")
        raise SystemExit(1)
    print("VERIFIED_DETERMINISTIC_KERNEL_REFINEMENT_AS_FACTORIZATION_SPECIAL_CASE")
    print("VERIFIED_STOCHASTIC_FACTORIZATION_PREORDER")
    print("VERIFIED_KERNEL_EQUALITY_INSUFFICIENT_FOR_STOCHASTIC_INFORMATION_ORDER")
    print("SURVIVED_CONSEQUENTIAL_INFORMATION_FACTORIZATION_V1")

if __name__=="__main__":
    run()
