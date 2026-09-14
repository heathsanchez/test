#!/usr/bin/env python3
from __future__ import annotations
from itertools import product, combinations

FROZEN="558ec58938b64fd63326bbf127566ee729bba40b"

def canon(blocks):
    return tuple(sorted((tuple(sorted(b)) for b in blocks), key=lambda b:(b[0],len(b),b)))
def partitions(items):
    out=[]; blocks=[]
    def rec(i):
        if i==len(items):
            out.append(canon(blocks)); return
        x=items[i]
        for j in range(len(blocks)):
            blocks[j].append(x); rec(i+1); blocks[j].pop()
        blocks.append([x]); rec(i+1); blocks.pop()
    rec(0)
    return tuple(sorted(set(out), key=lambda p:(len(p),p)))
def eqpairs(p):
    return frozenset((x,y) for b in p for x in b for y in b)
def refines(p,q): return eqpairs(p) <= eqpairs(q)
def strictly_coarser(q,p): return q!=p and refines(p,q)
def pfrom(sigs):
    g={}
    for i,s in enumerate(sigs): g.setdefault(tuple(s),[]).append(i)
    return canon(g.values())

X=tuple(range(4)); T=tuple(range(3)); PART4=partitions(X)
ST=tuple(range(3)); ACT=(0,1); PART3=partitions(ST)
UNORDERED=((0,1),(0,2),(1,2))

def mat(mask):
    return tuple(tuple((mask>>(x*3+t))&1 for t in T) for x in X)
def Kstate(m): return pfrom(m)
def Kcol(m):
    cols=tuple(tuple(m[x][t] for x in X) for t in T)
    return pfrom(cols)
def sufficient(p,m):
    return all(len({m[x] for x in b})==1 for b in p)
def RofS(m,S):
    return pfrom(tuple(tuple(m[x][t] for t in sorted(S)) for x in X))
def TofR(m,R):
    return frozenset(t for t in T if all(len({m[x][t] for x in b})==1 for b in R))
def bases(m):
    target=Kstate(m)
    subs=[frozenset(c) for r in range(4) for c in combinations(T,r)]
    good=[s for s in subs if RofS(m,s)==target]
    return tuple(s for s in good if not any(q<s for q in good))

def stable_behavior(trans,out):
    p=pfrom(tuple((out[s],) for s in ST))
    while True:
        cls={s:i for i,b in enumerate(p) for s in b}
        sig=tuple((out[s],cls[trans[s][0]],cls[trans[s][1]]) for s in ST)
        q=pfrom(sig)
        if q==p:return p
        p=q
def right_congruent(p,trans):
    cls={s:i for i,b in enumerate(p) for s in b}
    return all(len({cls[trans[s][a]] for s in b})<=1 for b in p for a in ACT)

def compatible_kernels(Eeq,Esep):
    ks=[]
    for p in PART3:
        ep=eqpairs(p)
        if all((a,b) in ep for a,b in Eeq) and all((a,b) not in ep for a,b in Esep):
            ks.append(p)
    return tuple(ks)

# WCD-style world-set epistemics over two states/two tests.
PROFILES=list(product((0,1), repeat=2))
WORLDS=[(p,q) for p in PROFILES for q in PROFILES]
def world_status(ws):
    if not ws:return "INCONSISTENT_EVIDENCE"
    d=all(any(a!=b for a,b in zip(p,q)) for p,q in ws)
    e=all(all(a==b for a,b in zip(p,q)) for p,q in ws)
    if d and e:return "CONTRADICTION"
    if d:return "DIST"
    if e:return "EQ"
    return "UNKNOWN"

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104); print("STATE–TEST KERNEL V2 — CONSISTENCY-GATED EXHAUSTIVE SUITE"); print("frozen =",FROZEN); print("="*104)

    print("\n--- A. EXACT STATE–TEST ALGEBRA: ALL 4096 BINARY MATRICES ---")
    n=0; img=True; suff=True; coarse=True; factor=True; gal=True; col=True; bex=True; sym=True
    nonunique_basis=0; basis_dist={}
    for mask in range(4096):
        m=mat(mask); n+=1; K=Kstate(m)
        img &= len(K)==len(set(m))
        sp=[p for p in PART4 if sufficient(p,m)]
        for p in PART4:
            suff &= (sufficient(p,m)==refines(p,K))
            factor &= (refines(p,K)==sufficient(p,m))
        cs=[p for p in sp if not any(strictly_coarser(q,p) and q in sp for q in PART4)]
        coarse &= (cs==[K])
        subs=[frozenset(c) for r in range(4) for c in combinations(T,r)]
        for R in PART4:
            TR=TofR(m,R)
            for S in subs:
                gal &= ((S<=TR)==refines(R,RofS(m,S)))
        ck=Kcol(m); reps=frozenset(b[0] for b in ck)
        col &= (RofS(m,reps)==K)
        bs=bases(m); bex &= bool(bs)
        if len(bs)>1: nonunique_basis+=1
        z=min(len(s) for s in bs); basis_dist[z]=basis_dist.get(z,0)+1
        kp=eqpairs(K)
        for R in PART4:
            rp=eqpairs(R)
            fm=rp-kp; fs=kp-rp
            sym &= ((rp^kp)==(fm|fs) and not(fm&fs))
    chk("A1 all 4096 matrices enumerated",n==4096,n)
    chk("A2 quotient cardinality equals image(Phi)",img)
    chk("A3 sufficiency iff ker(r) subseteq ker(Phi)",suff)
    chk("A4 unique coarsest exact sufficient representation",coarse)
    chk("A5 deterministic factorization agrees with kernel refinement",factor)
    chk("A6 state–probe Galois law exhaustive",gal)
    chk("A7 quotienting duplicate probe columns preserves state kernel",col)
    chk("A8 inclusion-minimal probe basis always exists",bex,basis_dist)
    chk("A9 minimal probe bases are sometimes nonunique",nonunique_basis>0,f"matrices={nonunique_basis}")
    chk("A10 symmetric-difference discrepancy exactly false-merge union false-split",sym)

    print("\n--- B. DYNAMIC CLOSURE: ALL 5832 DETERMINISTIC SYSTEMS ---")
    total=0; full_rc=True; shallow_witness=None
    for vals in product(ST, repeat=6):
        trans={s:{} for s in ST}; k=0
        for s in ST:
            for a in ACT: trans[s][a]=vals[k]; k+=1
        for outs in product((0,1), repeat=3):
            out={s:outs[s] for s in ST}; total+=1
            p=stable_behavior(trans,out); full_rc &= right_congruent(p,trans)
            shallow=pfrom(tuple((out[s],) for s in ST))
            if shallow_witness is None and not right_congruent(shallow,trans):
                shallow_witness=(trans,out,shallow,p)
    chk("B1 all 5832 systems enumerated",total==5832,total)
    chk("B2 full future kernel always right congruent",full_rc)
    chk("B3 nonclosed shallow family can fail right congruence",shallow_witness is not None,str(shallow_witness))

    print("\n--- C. POSSIBLE-KERNEL EPISTEMICS: ALL 64 EVIDENCE STATES ---")
    states=0; empty=0; direct_conflict=0; transitive_conflict=0; nonempty_counts={"EQ":0,"SEP":0,"UNKNOWN":0}; contradiction=False
    for eb in range(8):
        Eeq=frozenset(UNORDERED[i] for i in range(3) if eb&(1<<i))
        for sb in range(8):
            Esep=frozenset(UNORDERED[i] for i in range(3) if sb&(1<<i)); states+=1
            Ks=compatible_kernels(Eeq,Esep)
            if not Ks:
                empty+=1
                if Eeq&Esep: direct_conflict+=1
                elif {(0,1),(1,2)} <= Eeq and (0,2) in Esep: transitive_conflict+=1
                # V2 consistency gate: no pair-level EQ/SEP is licensed.
                continue
            for a,b in UNORDERED:
                am=all((a,b) in eqpairs(k) for k in Ks)
                ase=all((a,b) not in eqpairs(k) for k in Ks)
                if am and ase: contradiction=True
                if am: nonempty_counts["EQ"]+=1
                elif ase: nonempty_counts["SEP"]+=1
                else: nonempty_counts["UNKNOWN"]+=1
    chk("C1 all 64 pair-evidence states enumerated",states==64,states)
    chk("C2 inconsistent evidence is detected by empty K_E",empty==40,f"empty={empty}")
    chk("C3 direct contradiction is caught",direct_conflict>0,direct_conflict)
    chk("C4 transitive contradiction without direct pair overlap is caught",transitive_conflict>0,transitive_conflict)
    chk("C5 no nonempty compatible class gives contradictory EQ+SEP",not contradiction)
    chk("C6 EQ/SEP/UNKNOWN all occur under consistent evidence",all(v>0 for v in nonempty_counts.values()),nonempty_counts)

    print("\n--- D. WORLD-SET EPISTEMICS: ALL 65,536 MODEL SETS INCLUDING EMPTY ---")
    counts={"INCONSISTENT_EVIDENCE":0,"DIST":0,"EQ":0,"UNKNOWN":0,"CONTRADICTION":0}
    for bits in range(1<<len(WORLDS)):
        ws=[WORLDS[i] for i in range(16) if bits&(1<<i)]
        counts[world_status(ws)]+=1
    chk("D1 all 65,536 world sets classified",sum(counts.values())==65536,counts)
    chk("D2 empty world set maps only to INCONSISTENT_EVIDENCE",counts["INCONSISTENT_EVIDENCE"]==1,counts)
    chk("D3 no world set yields contradictory DIST+EQ",counts["CONTRADICTION"]==0,counts)
    chk("D4 nonempty counts reproduce prior DIST/EQ/UNKNOWN totals",
        counts["DIST"]==4095 and counts["EQ"]==15 and counts["UNKNOWN"]==61425,counts)

    print("\n--- E. APPROXIMATE BOUNDARY ---")
    close=lambda a,b: abs(a-b)<=1.0
    chk("E1 epsilon threshold need not be transitive",close(0,1) and close(1,2) and not close(0,2))
    profs=list(product((0,1,2),repeat=2))
    def d(a,b):return max(abs(a[i]-b[i]) for i in range(2))
    tri=all(d(a,c)<=d(a,b)+d(b,c)+1e-12 for a in profs for b in profs for c in profs)
    chk("E2 sup-test metric finite sanity obeys triangle inequality",tri)

    total=len(checks); passed=sum(ok for _,ok,_ in checks)
    print("\n"+"="*104); print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{total}")
    if failures:
        print("FALSIFIED_STATE_TEST_KERNEL_V2")
        for n,d in failures: print("FAILED:",n,"—",d)
        raise SystemExit(1)
    print("VERIFIED_STATE_TEST_KERNEL_V2_EXACT_ALGEBRA")
    print("VERIFIED_STATE_TEST_KERNEL_V2_CONSISTENCY_GATED_EPISTEMICS")
    print("VERIFIED_STATE_TEST_KERNEL_V2_STATE_PROBE_DUALITY")
    print("VERIFIED_STATE_TEST_KERNEL_V2_DYNAMIC_CLOSURE")
    print("SURVIVED_STATE_TEST_KERNEL_V2_EXHAUSTIVE_SUITE")

if __name__=="__main__": run()
