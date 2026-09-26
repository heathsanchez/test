#!/usr/bin/env python3
"""Find explicit recurrent blocked 3-adic cycles and classify coefficient drift.

A cycle with k shortcut edges and q odd edges has linear multiplier 3^q/2^k.
If blocked 3-adic context admits a nonnegative-drift cycle, then neither
3-adic blockage nor coefficient/chamber sign alone forces escape; the exact
2-adic realization/M register is necessary.
"""
from itertools import combinations
import json
O=12;S=19;M=3**O;inv2=pow(2,-1,M)
def comps(total,parts):
    for cuts in combinations(range(1,total),parts-1):
        p=0;w=[]
        for c in cuts+(total,):w.append(c-p);p=c
        yield w
def C(w):
    x=0
    for i,a in enumerate(w):x=(1<<a)*x+3**i
    return x
A={(C(w)*pow(1<<S,-1,M))%M for w in comps(S,O)}
blocked={r for r in range(M) if r%3 and r not in A}
def step(r,b):return ((r*inv2)%M) if b==0 else ((3*r+1)*inv2)%M

# Immediate fixed points/cycles first.
fixed=[]
for r in blocked:
    for b in (0,1):
        if step(r,b)==r:
            fixed.append((r,b))
# -1 mod 3^12 is the odd-map fixed point.
minus1=M-1
assert step(minus1,1)==minus1
minus1_blocked=minus1 in blocked

# Search short blocked cycles by DFS from small states, tracking labels.
found=[]
maxlen=16
for start in sorted(blocked)[:5000]:
    stack=[(start,[],[start])]
    while stack and len(found)<30:
        r,bits,path=stack.pop()
        if len(bits)>=maxlen:continue
        for b in (0,1):
            y=step(r,b)
            if y not in blocked:continue
            nb=bits+[b]
            if y==start:
                q=sum(nb);k=len(nb)
                found.append({"start":start,"bits":"".join(map(str,nb)),"k":k,"q":q,
                              "drift":"NONNEGATIVE" if 3**q>=2**k else "NEGATIVE"})
                continue
            if y not in path:
                stack.append((y,nb,path+[y]))
        if len(found)>=30:break
    if len(found)>=30:break
nonneg=[x for x in found if x["drift"]=="NONNEGATIVE"]
result={
 "schema":"COLLATZ_BLOCKED_CONTEXT_WEIGHTED_CYCLES_V0",
 "minus1_residue":minus1,"minus1_blocked":minus1_blocked,
 "fixed_points":[{"residue":r,"edge":"ODD" if b else "EVEN",
                  "drift":"NONNEGATIVE" if (b and 3>=2) else "NEGATIVE"} for r,b in fixed[:20]],
 "short_cycles_found":len(found),"nonnegative_drift_short_cycles":len(nonneg),
 "sample_nonnegative":nonneg[:10],
 "decision":"JOINT_2ADIC_M_REGISTER_NECESSARY" if minus1_blocked or nonneg else "NO_NONNEGATIVE_BLOCKED_CYCLE_FOUND",
 "scope_warning":"these are symbolic 3-adic cycles; integer/canonical M>=0 reachability is not implied",
 "next":"use canonical realization R=-B*(3^q)^-1 mod 2^k and M to reject symbolic blocked cycles/paths; do not enlarge 3-adic precision alone",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
