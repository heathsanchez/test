#!/usr/bin/env python3
"""
State-Test Kernel V1 — exhaustive falsification suite.

Frozen candidate:
  9e6102ab8e1b1f2b3e10ae663a56d8178c975d3a

The suite intentionally includes inconsistent finite evidence states to test
whether the possible-kernel EQ/SEP/UNKNOWN rule is total and contradiction-free.
A candidate failure exits nonzero.
"""
from __future__ import annotations

from itertools import product, combinations
from typing import FrozenSet, Iterable, List, Sequence, Tuple

FROZEN = "9e6102ab8e1b1f2b3e10ae663a56d8178c975d3a"

# ---------- partition utilities ----------

def canon(blocks):
    return tuple(sorted((tuple(sorted(b)) for b in blocks), key=lambda b: (b[0], len(b), b)))

def partitions(items: Sequence[int]):
    out=[]
    blocks=[]
    def rec(i):
        if i == len(items):
            out.append(canon(blocks))
            return
        x=items[i]
        for j in range(len(blocks)):
            blocks[j].append(x); rec(i+1); blocks[j].pop()
        blocks.append([x]); rec(i+1); blocks.pop()
    rec(0)
    return tuple(sorted(set(out), key=lambda p:(len(p),p)))

def eqpairs(part):
    s=set()
    for b in part:
        for x in b:
            for y in b:
                s.add((x,y))
    return frozenset(s)

def refines(p,q):
    # p is at least as informative/fine as q
    return eqpairs(p) <= eqpairs(q)

def strictly_coarser(q,p):
    return q != p and refines(p,q)

def partition_from_signatures(sigs):
    groups={}
    for i,s in enumerate(sigs):
        groups.setdefault(tuple(s),[]).append(i)
    return canon(groups.values())

# ---------- evaluation matrices ----------

X=tuple(range(4))
T=tuple(range(3))
PART4=partitions(X)
assert len(PART4)==15

def matrix_from_mask(mask:int):
    # rows x tests, binary consequence
    return tuple(tuple((mask >> (x*len(T)+t)) & 1 for t in T) for x in X)

def state_kernel(mat):
    return partition_from_signatures(mat)

def col_vectors(mat):
    return tuple(tuple(mat[x][t] for x in X) for t in T)

def col_kernel(mat):
    return partition_from_signatures(col_vectors(mat))

def sufficient(rep_part, mat):
    # Phi factors through r iff rows are equal inside every rep block.
    for b in rep_part:
        rows={mat[x] for x in b}
        if len(rows)>1:
            return False
    return True

def R_of_S(mat, S:FrozenSet[int]):
    return partition_from_signatures(tuple(tuple(mat[x][t] for t in sorted(S)) for x in X))

def T_of_R(mat, R):
    good=[]
    for t in T:
        ok=True
        for b in R:
            vals={mat[x][t] for x in b}
            if len(vals)>1: ok=False; break
        if ok: good.append(t)
    return frozenset(good)

def minimal_probe_bases(mat):
    full=state_kernel(mat)
    subsets=[frozenset(s) for r in range(len(T)+1) for s in combinations(T,r)]
    good=[s for s in subsets if R_of_S(mat,s)==full]
    return tuple(s for s in good if not any(q < s for q in good))

# ---------- dynamic systems ----------

ST=tuple(range(3))
ACT=(0,1)

def stable_behavior_partition(trans, out):
    # start from current observable consequence then refine by successor classes
    p=partition_from_signatures(tuple((out[s],) for s in ST))
    while True:
        cls={}
        for i,b in enumerate(p):
            for s in b: cls[s]=i
        sigs=tuple((out[s],)+(tuple(cls[trans[s][a]] for a in ACT)) for s in ST)
        q=partition_from_signatures(sigs)
        if q==p: return p
        p=q

def right_congruent(part, trans):
    cls={}
    for i,b in enumerate(part):
        for s in b: cls[s]=i
    for b in part:
        for a in ACT:
            if len({cls[trans[s][a]] for s in b})>1:
                return False
    return True

# ---------- possible-kernel epistemic model ----------

PART3=partitions(ST)
UNORDERED=((0,1),(0,2),(1,2))

def compatible_kernels(Eeq, Esep):
    out=[]
    for p in PART3:
        ep=eqpairs(p)
        if all((a,b) in ep and (b,a) in ep for a,b in Eeq) and all((a,b) not in ep for a,b in Esep):
            out.append(p)
    return tuple(out)

def candidate_commitments(Ks, pair):
    a,b=pair
    all_merge=all((a,b) in eqpairs(k) for k in Ks)
    all_sep=all((a,b) not in eqpairs(k) for k in Ks)
    return all_merge, all_sep

def run():
    checks=[]
    failures=[]
    def chk(name, cond, detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("STATE–TEST KERNEL V1 — EXHAUSTIVE FALSIFICATION SUITE")
    print("frozen =",FROZEN)
    print("="*104)

    # A. All 4096 binary evaluation matrices.
    print("\n--- A. ALL 4x3 BINARY EVALUATION MATRICES ---")
    nmat=0
    quotient_image=True
    suff_iff_kernel=True
    unique_coarsest=True
    factor_order=True
    galois=True
    col_collapse=True
    basis_exists=True
    symdiff_complete=True
    basis_sizes={}

    for mask in range(1<<(len(X)*len(T))):
        mat=matrix_from_mask(mask); nmat+=1
        K=state_kernel(mat)

        # quotient blocks = distinct Phi rows
        quotient_image &= (len(K)==len(set(mat)))

        suff_parts=[p for p in PART4 if sufficient(p,mat)]
        for p in PART4:
            # sufficiency iff representation kernel subset future kernel
            suff_iff_kernel &= (sufficient(p,mat) == refines(p,K))
            # deterministic factorization r >= Phi is same refinement condition
            factor_order &= (refines(p,K) == sufficient(p,mat))

        coarsest=[p for p in suff_parts if not any(strictly_coarser(q,p) and q in suff_parts for q in PART4)]
        unique_coarsest &= (coarsest == [K])

        # Galois law over every state equivalence and every probe subset.
        subsets=[frozenset(s) for r in range(len(T)+1) for s in combinations(T,r)]
        for R in PART4:
            TR=T_of_R(mat,R)
            for S in subsets:
                left = S <= TR
                right = refines(R, R_of_S(mat,S))
                if left != right:
                    galois=False

        # quotient duplicate columns; one representative per equal column class
        ck=col_kernel(mat)
        reps=frozenset(b[0] for b in ck)
        col_collapse &= (R_of_S(mat,reps)==K)

        bases=minimal_probe_bases(mat)
        basis_exists &= bool(bases)
        m=min(len(s) for s in bases)
        basis_sizes[m]=basis_sizes.get(m,0)+1

        # current representation discrepancy decomposes into false merge/split.
        kp=eqpairs(K)
        for R in PART4:
            rp=eqpairs(R)
            sym=rp ^ kp
            false_merge=rp-kp
            false_split=kp-rp
            symdiff_complete &= (sym == false_merge | false_split and not (false_merge & false_split))

    chk("A1 enumerated all 4096 binary 4x3 evaluation matrices", nmat==4096, nmat)
    chk("A2 quotient cardinality always equals image(Phi) cardinality", quotient_image)
    chk("A3 exact sufficiency iff ker(r) subseteq ker(Phi)", suff_iff_kernel)
    chk("A4 future-consequence quotient is unique coarsest exact sufficient partition", unique_coarsest)
    chk("A5 deterministic factorization order agrees with kernel refinement", factor_order)
    chk("A6 state-probe Galois law holds for every partition/probe subset", galois)
    chk("A7 collapsing duplicate probe columns preserves full state kernel", col_collapse)
    chk("A8 every finite evaluation matrix has an inclusion-minimal probe basis", basis_exists, basis_sizes)
    chk("A9 representation error always decomposes into false merges + false splits", symdiff_complete)

    # B. Dynamic closure across all 3-state, 2-action deterministic systems.
    print("\n--- B. ALL 3-STATE / 2-ACTION DETERMINISTIC SYSTEMS ---")
    total=0
    full_future_right_congruent=True
    nonclosed_witness=None

    # transition table flattened (s,a): 6 choices each in 0..2 => 3^6
    for vals in product(ST, repeat=len(ST)*len(ACT)):
        trans={s:{} for s in ST}
        k=0
        for s in ST:
            for a in ACT:
                trans[s][a]=vals[k]; k+=1
        for outs in product((0,1), repeat=len(ST)):
            out={s:outs[s] for s in ST}; total+=1
            p=stable_behavior_partition(trans,out)
            if not right_congruent(p,trans):
                full_future_right_congruent=False

            shallow=partition_from_signatures(tuple((out[s],) for s in ST))
            if not right_congruent(shallow,trans) and nonclosed_witness is None:
                nonclosed_witness=(trans,out,shallow,p)

    chk("B1 enumerated all 5832 deterministic systems", total==5832, total)
    chk("B2 full future behavioral kernel is always right congruent", full_future_right_congruent)
    chk("B3 non-closed shallow test family can fail right congruence", nonclosed_witness is not None, str(nonclosed_witness))

    # C. UNKNOWN via possible kernels: exhaustive evidence assignments on 3 pairs.
    print("\n--- C. POSSIBLE-KERNEL EPISTEMIC RULE ---")
    evidence_states=0
    empty_models=[]
    contradictory_commitments=[]
    nonempty_contradiction=False
    nonempty_threeway={"EQ":0,"SEP":0,"UNKNOWN":0}

    # independently choose Eeq and Esep subsets: 8 x 8 = 64
    for eqbits in range(1<<len(UNORDERED)):
        Eeq=frozenset(UNORDERED[i] for i in range(len(UNORDERED)) if eqbits&(1<<i))
        for sepbits in range(1<<len(UNORDERED)):
            Esep=frozenset(UNORDERED[i] for i in range(len(UNORDERED)) if sepbits&(1<<i))
            evidence_states+=1
            Ks=compatible_kernels(Eeq,Esep)
            if not Ks:
                empty_models.append((Eeq,Esep))
            for pair in UNORDERED:
                m,s=candidate_commitments(Ks,pair)
                if m and s:
                    contradictory_commitments.append((Eeq,Esep,pair,len(Ks)))
                    if Ks: nonempty_contradiction=True
                if Ks:
                    if m and not s: nonempty_threeway["EQ"]+=1
                    elif s and not m: nonempty_threeway["SEP"]+=1
                    elif not m and not s: nonempty_threeway["UNKNOWN"]+=1

    chk("C1 enumerated all 64 finite evidence assignments", evidence_states==64, evidence_states)
    chk("C2 some evidence assignments make K_E empty", len(empty_models)>0, f"empty={len(empty_models)}")
    # This is the key candidate falsifier.
    chk("C3 frozen possible-kernel rule is contradiction-free on ALL evidence assignments",
        len(contradictory_commitments)==0,
        f"contradictions={len(contradictory_commitments)} first={contradictory_commitments[:1]}")
    chk("C4 when K_E is nonempty, EQ/SEP commitments never conflict",
        not nonempty_contradiction,
        nonempty_threeway)
    chk("C5 nonempty models genuinely realize EQ, SEP, and UNKNOWN",
        all(nonempty_threeway[k]>0 for k in nonempty_threeway),
        nonempty_threeway)

    # D. Approximate boundary.
    print("\n--- D. APPROXIMATE BOUNDARY ---")
    # One test, scalar consequence metric |.|, epsilon=1:
    # 0~1 and 1~2 but 0 !~ 2, hence threshold relation is non-transitive.
    vals=(0.0,1.0,2.0); eps=1.0
    close=lambda a,b: abs(a-b)<=eps
    chk("D1 epsilon-closeness can be non-transitive",
        close(vals[0],vals[1]) and close(vals[1],vals[2]) and not close(vals[0],vals[2]))
    # sup of metric coordinates is a pseudometric; finite sanity over profiles.
    profs=list(product((0,1,2), repeat=2))
    triangle=True
    def d(a,b): return max(abs(a[i]-b[i]) for i in range(2))
    for a in profs:
        for b in profs:
            for c in profs:
                if d(a,c) > d(a,b)+d(b,c)+1e-12: triangle=False
    chk("D2 finite sup-test distance obeys triangle inequality", triangle)

    n=sum(ok for _,ok,_ in checks); total=len(checks)
    print("\n"+"="*104)
    print(f"VERDICT: {'PASS' if not failures else 'FALSIFIED'} {n}/{total}")
    if failures:
        print("FALSIFIED_STATE_TEST_KERNEL_V1")
        for name,detail in failures:
            print("FAILED:",name,"—",detail)
        raise SystemExit(1)
    else:
        print("SURVIVED_STATE_TEST_KERNEL_V1_EXHAUSTIVE_SUITE")

if __name__=="__main__":
    run()
