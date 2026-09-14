#!/usr/bin/env python3
"""
State-Test Kernel V2 boundary tests.

1. Exhaustively quantify whether greedy pair-separation finds a minimum probe
   basis over every binary 5-state x 4-probe evaluation matrix (32^4=1,048,576).
2. Test whether exact kernel equality is sufficient to order stochastic
   representations, using exact rational channels.

These are boundary tests: they do not alter State-Test Kernel V2.
"""
from fractions import Fraction as F
from itertools import combinations, product

NSTATE=5
NTEST=4
ALL_STATES=tuple(range(NSTATE))
ALL_TESTS=tuple(range(NTEST))
SUBSETS=[tuple(c) for r in range(NTEST+1) for c in combinations(ALL_TESTS,r)]

def bit(col, s):
    return (col >> s) & 1

def signature(cols, s, subset):
    return tuple(bit(cols[t],s) for t in subset)

def target_classes(cols):
    d={}
    for s in ALL_STATES:
        d.setdefault(signature(cols,s,ALL_TESTS),[]).append(s)
    return tuple(sorted(tuple(v) for v in d.values()))

def classes(cols, subset):
    d={}
    for s in ALL_STATES:
        d.setdefault(signature(cols,s,subset),[]).append(s)
    return tuple(sorted(tuple(v) for v in d.values()))

def merged_pairs(part):
    return sum(len(b)*(len(b)-1)//2 for b in part)

def min_basis_size(cols, target):
    for r in range(NTEST+1):
        for sub in combinations(ALL_TESTS,r):
            if classes(cols,sub)==target:
                return r
    raise AssertionError

def greedy_basis(cols, target):
    chosen=[]
    remain=set(ALL_TESTS)
    while classes(cols,tuple(sorted(chosen))) != target:
        opts=[]
        for t in sorted(remain):
            p=classes(cols,tuple(sorted(chosen+[t])))
            opts.append((merged_pairs(p),t))
        _,t=min(opts)
        chosen.append(t); remain.remove(t)
    return tuple(chosen)

def stochastic_boundary():
    # Representation/channel r1: perfect state revelation.
    # Rows are P(output | state).
    r1=((F(1),F(0)),(F(0),F(1)))
    # r2: BSC(1/4), a stochastic garbling of r1.
    r2=((F(3,4),F(1,4)),(F(1,4),F(3,4)))
    # r3: constant/no-information channel.
    r3=((F(1,2),F(1,2)),(F(1,2),F(1,2)))

    def kernel(ch):
        return "DISCRETE" if ch[0] != ch[1] else "MERGED"

    # Exact forward garbling r1 -> r2 is the BSC itself.
    G=((F(3,4),F(1,4)),(F(1,4),F(3,4)))

    def row_times_channel(row, M):
        return tuple(sum(row[i]*M[i][j] for i in range(2)) for j in range(2))

    forward=tuple(row_times_channel(row,G) for row in r1)

    # Reverse would require H parameters a=P(z0|y0), b=P(z0|y1):
    # 3a+b=4 and a+3b=0. Exact solution a=3/2,b=-1/2, invalid.
    a=F(3,2); b=F(-1,2)
    reverse_candidate_valid=(F(0)<=a<=F(1) and F(0)<=b<=F(1))

    # r2 -> r3 by output-forgetting channel.
    Hforget=((F(1,2),F(1,2)),(F(1,2),F(1,2)))
    to_constant=tuple(row_times_channel(row,Hforget) for row in r2)

    return {
        "r1_kernel":kernel(r1),
        "r2_kernel":kernel(r2),
        "r3_kernel":kernel(r3),
        "r1_to_r2_exact":forward==r2,
        "r2_to_r1_stochastic_possible":reverse_candidate_valid,
        "reverse_linear_solution":(str(a),str(b)),
        "r2_to_r3_exact":to_constant==r3,
    }

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("STATE–TEST KERNEL V2 — SEARCH/CHANNEL BOUNDARY TESTS")
    print("="*104)

    print("\n--- A. EXHAUSTIVE GREEDY PROBE ACQUISITION ---")
    total=0; failures_greedy=0; max_overhead=0; first=None
    dist={}
    # Four binary probe columns, each a 5-bit vector => 32^4 matrices.
    for cols in product(range(1<<NSTATE), repeat=NTEST):
        total+=1
        target=target_classes(cols)
        opt=min_basis_size(cols,target)
        g=greedy_basis(cols,target)
        overhead=len(g)-opt
        dist[(opt,len(g))]=dist.get((opt,len(g)),0)+1
        if overhead>0:
            failures_greedy+=1
            if first is None:
                first=(cols,target,opt,g)
            max_overhead=max(max_overhead,overhead)

    chk("A1 enumerated all 1,048,576 binary 5x4 evaluation matrices",total==1048576,total)
    chk("A2 greedy immediate pair-separation is NOT universally minimum-cardinality",
        failures_greedy>0,
        f"greedy_suboptimal={failures_greedy} first={first}")
    chk("A3 quantified a positive maximum greedy overhead",max_overhead>0,max_overhead)
    print("probe_size_distribution",sorted(dist.items()))

    print("\n--- B. STOCHASTIC CHANNEL ORDER ---")
    s=stochastic_boundary()
    chk("B1 perfect and noisy channels have the same exact kernel",
        s["r1_kernel"]==s["r2_kernel"]=="DISCRETE",s)
    chk("B2 noisy channel is an exact stochastic garbling of perfect channel",
        s["r1_to_r2_exact"],s)
    chk("B3 reverse stochastic recovery is impossible",
        not s["r2_to_r1_stochastic_possible"],s["reverse_linear_solution"])
    chk("B4 noisy channel can be further garbled to no-information channel",
        s["r2_to_r3_exact"],s)
    chk("B5 exact kernel equality therefore does not determine stochastic information order",
        s["r1_kernel"]==s["r2_kernel"] and s["r1_to_r2_exact"] and not s["r2_to_r1_stochastic_possible"])

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
