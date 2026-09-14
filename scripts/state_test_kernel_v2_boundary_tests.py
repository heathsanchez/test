#!/usr/bin/env python3
"""
State-Test Kernel V2 boundary tests — optimized exhaustive version.

1. Exhaustively quantify greedy probe-selection suboptimality across every
   binary 5-state x 4-probe evaluation matrix: 32^4 = 1,048,576 matrices.
2. Test whether exact kernel equality is sufficient to order stochastic
   representations, using exact rational channels.

This version uses bitmasks over the 10 unordered state pairs so the exhaustive
probe search is fast and exact.
"""
from fractions import Fraction as F
from itertools import combinations, product

NSTATE=5
NTEST=4
PAIRS=tuple((i,j) for i in range(NSTATE) for j in range(i+1,NSTATE))

# Each binary probe column is a 5-bit vector. Map it to the set of unordered
# state pairs it separates, encoded as a 10-bit mask.
SEP_MASK=[]
for col in range(1<<NSTATE):
    m=0
    for k,(i,j) in enumerate(PAIRS):
        if ((col>>i)&1) != ((col>>j)&1):
            m |= 1<<k
    SEP_MASK.append(m)

SUBSETS_BY_SIZE={
    r:tuple(combinations(range(NTEST),r))
    for r in range(NTEST+1)
}

def union_mask(ms, subset):
    u=0
    for i in subset:
        u |= ms[i]
    return u

def min_basis_size(ms,target):
    if target==0:
        return 0
    for r in range(1,NTEST+1):
        for sub in SUBSETS_BY_SIZE[r]:
            if union_mask(ms,sub)==target:
                return r
    raise AssertionError

def greedy_size(ms,target):
    remaining=target
    chosen=set()
    n=0
    while remaining:
        best=None
        for i,m in enumerate(ms):
            if i in chosen:
                continue
            gain=(m & remaining).bit_count()
            cand=(-gain,i)
            if best is None or cand<best[0]:
                best=(cand,i)
        i=best[1]
        chosen.add(i)
        n+=1
        remaining &= ~ms[i]
    return n

def stochastic_boundary():
    # r1: perfect state revelation.
    r1=((F(1),F(0)),(F(0),F(1)))
    # r2: binary symmetric channel with crossover 1/4.
    r2=((F(3,4),F(1,4)),(F(1,4),F(3,4)))
    # r3: no-information channel.
    r3=((F(1,2),F(1,2)),(F(1,2),F(1,2)))

    def kernel(ch):
        return "DISCRETE" if ch[0] != ch[1] else "MERGED"

    def row_times_channel(row,M):
        return tuple(sum(row[i]*M[i][j] for i in range(2)) for j in range(2))

    G=((F(3,4),F(1,4)),(F(1,4),F(3,4)))
    forward=tuple(row_times_channel(row,G) for row in r1)

    # Reverse recovery r2 -> r1 would require:
    # 3a+b=4 and a+3b=0, hence a=3/2,b=-1/2, not stochastic.
    a=F(3,2); b=F(-1,2)

    Hforget=((F(1,2),F(1,2)),(F(1,2),F(1,2)))
    to_constant=tuple(row_times_channel(row,Hforget) for row in r2)

    return {
        "r1_kernel":kernel(r1),
        "r2_kernel":kernel(r2),
        "r3_kernel":kernel(r3),
        "r1_to_r2_exact":forward==r2,
        "r2_to_r1_stochastic_possible":F(0)<=a<=F(1) and F(0)<=b<=F(1),
        "reverse_linear_solution":(str(a),str(b)),
        "r2_to_r3_exact":to_constant==r3,
    }

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond:
            failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("STATE–TEST KERNEL V2 — SEARCH/CHANNEL BOUNDARY TESTS")
    print("="*104)

    print("\n--- A. EXHAUSTIVE GREEDY PROBE ACQUISITION ---")
    total=0
    suboptimal=0
    max_overhead=0
    first=None
    dist={}

    for cols in product(range(1<<NSTATE), repeat=NTEST):
        total+=1
        ms=tuple(SEP_MASK[c] for c in cols)
        target=ms[0]|ms[1]|ms[2]|ms[3]
        opt=min_basis_size(ms,target)
        g=greedy_size(ms,target)
        dist[(opt,g)]=dist.get((opt,g),0)+1
        if g>opt:
            suboptimal+=1
            max_overhead=max(max_overhead,g-opt)
            if first is None:
                first={
                    "columns":cols,
                    "separation_masks":ms,
                    "target_mask":target,
                    "optimal_size":opt,
                    "greedy_size":g,
                }

    chk("A1 enumerated all 1,048,576 binary 5x4 evaluation matrices",total==1048576,total)
    chk("A2 greedy immediate pair-separation is not universally optimal",
        suboptimal>0,
        f"suboptimal={suboptimal} ({100*suboptimal/total:.6f}%) first={first}")
    chk("A3 exact suboptimal count is 29,760",suboptimal==29760,suboptimal)
    chk("A4 maximum greedy overhead is one probe",max_overhead==1,max_overhead)
    chk("A5 full optimal-vs-greedy distribution matches exhaustive census",
        dist=={
            (0,0):16,
            (1,1):3600,
            (2,2):295200,
            (3,3):672000,
            (2,3):22080,
            (4,4):48000,
            (3,4):7680,
        },
        sorted(dist.items()))

    print("\n--- B. STOCHASTIC CHANNEL ORDER ---")
    s=stochastic_boundary()
    chk("B1 perfect and noisy channels have the same exact kernel",
        s["r1_kernel"]==s["r2_kernel"]=="DISCRETE",s)
    chk("B2 noisy channel is a stochastic garbling of perfect channel",
        s["r1_to_r2_exact"],s)
    chk("B3 reverse stochastic recovery is impossible",
        not s["r2_to_r1_stochastic_possible"],s["reverse_linear_solution"])
    chk("B4 noisy channel further garbles to no-information channel",
        s["r2_to_r3_exact"],s)
    chk("B5 exact kernel equality does not determine stochastic information order",
        s["r1_kernel"]==s["r2_kernel"]
        and s["r1_to_r2_exact"]
        and not s["r2_to_r1_stochastic_possible"])

    passed=sum(ok for _,ok,_ in checks); totalc=len(checks)
    print("\n"+"="*104)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{totalc}")
    if failures:
        raise SystemExit(1)
    print("VERIFIED_STATE_TEST_DUALITY_DOES_NOT_IMPLY_GREEDY_PROBE_OPTIMALITY")
    print("VERIFIED_STOCHASTIC_INFORMATION_ORDER_STRICTLY_REFINES_EXACT_KERNEL_EQUALITY")
    print("STATE_TEST_KERNEL_V2_BOUNDARY_TESTS_PASS")

if __name__=="__main__":
    run()
