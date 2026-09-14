#!/usr/bin/env python3
from itertools import product, combinations

FROZEN="46ab2f010255211f368c421e70011d9b3bf4a18d"

PROFILES=list(product((0,1),repeat=2))
WORLDS=[(p,q) for p in PROFILES for q in PROFILES]

def v1_status(ws):
    d=all(any(a!=b for a,b in zip(p,q)) for p,q in ws)
    e=all(all(a==b for a,b in zip(p,q)) for p,q in ws)
    if d and e:return "CONTRADICTION"
    if d:return "DIST"
    if e:return "EQ"
    return "UNKNOWN"

def v2_status(ws):
    if not ws:return "INCONSISTENT_EVIDENCE"
    return v1_status(ws)

def rsep(ws):
    if not ws:return False
    return any(all(w[0][i]!=w[1][i] for w in ws) for i in range(2))

def run():
    checks=[]; fail=[]
    def chk(n,c,d=""):
        checks.append((n,bool(c),d))
        if not c: fail.append((n,d))
        print(f"  [{'PASS' if c else 'FAIL'}] {n}" + (f" — {d}" if d else ""))

    print("="*100); print("WCD V2 CONSISTENCY-GATED EXHAUSTIVE SUITE"); print("frozen =",FROZEN); print("="*100)

    counts={"INCONSISTENT_EVIDENCE":0,"DIST":0,"EQ":0,"UNKNOWN":0,"CONTRADICTION":0}
    same_nonempty=True; rsep_implies=True; dist_without_rsep=None
    for bits in range(1<<16):
        ws=[WORLDS[i] for i in range(16) if bits&(1<<i)]
        s2=v2_status(ws); counts[s2]+=1
        if ws and s2!=v1_status(ws): same_nonempty=False
        if rsep(ws) and s2!="DIST": rsep_implies=False
        if ws and s2=="DIST" and not rsep(ws) and dist_without_rsep is None:
            dist_without_rsep=ws

    chk("A1 all 65,536 world sets classified",sum(counts.values())==65536,counts)
    chk("A2 empty set maps only to INCONSISTENT_EVIDENCE",counts["INCONSISTENT_EVIDENCE"]==1,counts)
    chk("A3 no consistent set produces DIST/EQ contradiction",counts["CONTRADICTION"]==0,counts)
    chk("A4 every nonempty world set matches frozen WCD V1 exactly",same_nonempty)
    chk("A5 nonempty counts reproduce V1 totals",counts["DIST"]==4095 and counts["EQ"]==15 and counts["UNKNOWN"]==61425,counts)
    chk("A6 RSEP always implies DIST",rsep_implies)
    chk("A7 DIST can hold without one common robust separator",dist_without_rsep is not None,str(dist_without_rsep))

    # Joint-configuration attack: all 256 Boolean functions on three features.
    feats=("a","b","c")
    cfgs=[frozenset(c) for r in range(4) for c in combinations(feats,r)]
    def idx(c): return sum((1<<i) for i,f in enumerate(feats) if f in c)
    def val(mask,c): return (mask>>idx(c))&1
    def frontier(mask):
        good=[c for c in cfgs if val(mask,c)==1]
        return [c for c in good if not any(q<c and val(mask,q)==1 for q in good)]
    synergy=None; incomparable=None
    for mask in range(256):
        fr=frontier(mask)
        if len(fr)>1 and incomparable is None: incomparable=(mask,fr)
        full=frozenset(feats)
        if val(mask,full)==1 and all(val(mask,full-{f})==1 for f in feats) and val(mask,frozenset())==0:
            if synergy is None: synergy=(mask,fr)
    chk("B1 incomparable lawful minima exist",incomparable is not None,str(incomparable))
    chk("B2 non-additive joint-sufficiency witness exists",synergy is not None,str(synergy))

    # Ground/preference sanity.
    cands=[("cheap_invalid",False,0),("valid_slow",True,10),("valid_fast",True,3)]
    lawful=[c for c in cands if c[1]]
    chosen=min(lawful,key=lambda x:x[2])[0]
    chk("C1 ground dominates preference",chosen=="valid_fast",chosen)

    n=sum(c for _,c,_ in checks); total=len(checks)
    print("="*100); print(f"VERDICT: {'PASS' if not fail else 'FAIL'} {n}/{total}")
    if fail:
        print("FALSIFIED_WCD_V2")
        raise SystemExit(1)
    print("VERIFIED_WCD_V2_CONSISTENCY_GATE")
    print("VERIFIED_WCD_V2_NONEMPTY_EQUIVALENCE_TO_V1")
    print("SURVIVED_WCD_V2_EXHAUSTIVE_SUITE")

if __name__=="__main__":run()
