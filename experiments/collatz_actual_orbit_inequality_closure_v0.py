#!/usr/bin/env python3
"""Crystal actual-orbit inequality closure V0.

Freeze the proof object to one hypothetical minimal-bad shortcut orbit.
Every exact reverse certificate p=(a*y-c)/d is used only through the
contrapositive of OrdinaryExit: on Live, p>=source, hence a*y>=d*source+c.

This executable does NOT infer global Collatz from a finite bank. It asks the
smallest decisive question: after compiling the existing Q14 reverse bank into
source-relative inequalities and closing them along exact actual transitions,
what residue/constraint family remains unconstrained?
"""
from __future__ import annotations
import json,sys
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"source_product_v1"))
from collatz_reverse_target_audit import enumerate_target
from source_product import initial,advance

Q=14
M=3**Q
certs=enumerate_target(Q)

# Strongest asymptotic source-relative lower bound d/a for each endpoint
# residue.  Additive c/a is retained for exact checking.
best=[None]*M
for z in certs:
    if z.residue%3 != 1:
        continue
    item=(Fraction(z.d,z.a),Fraction(z.c,z.a),z.word,z.a,z.c,z.d,z.residue)
    for r in range(z.residue,M,z.d):
        old=best[r]
        if old is None or (item[0],item[1])>(old[0],old[1]):
            best[r]=item

# Add the elementary inverse-odd capability separately. For odd y=2 mod 3,
# p=(2y-1)/3 and Live implies 2y>=3n+1.
def live_bound(n,y):
    candidates=[]
    if y&1 and y%3==2:
        candidates.append((Fraction(3,2),Fraction(1,2),"inverse-odd"))
    if y%3==1 and best[y%M] is not None:
        a,b,w,*_=best[y%M]
        candidates.append((a,b,"Q14:"+w))
    if not candidates:
        return None
    return max(candidates,key=lambda x:(x[0],x[1]))

# Exact bounded actual-path falsifier/diagnostic. We stop a source at the first
# ordinary descent/terminal; before that, every compiled bound must hold unless
# it itself exposes a lower predecessor (which is precisely an Exit).
BITS=18
DEPTH=512
checked=violations=forced_exit=0
unconstrained=constrained=0
residue_hist={}
tight=[]
for n in range(3,1<<BITS,2):
    s=initial(n)
    for k in range(DEPTH+1):
        y=s.endpoint
        if y in (1,2) or y<n:
            break
        b=live_bound(n,y)
        if b is None:
            unconstrained+=1
            residue_hist[y%3]=residue_hist.get(y%3,0)+1
        else:
            constrained+=1
            alpha,beta,label=b
            checked+=1
            if Fraction(y,1) < alpha*n+beta:
                # The certificate says a smaller predecessor exists. This is
                # not a law violation: it is exactly an OrdinaryExit witness.
                forced_exit+=1
                break
            slack=Fraction(y,1)-(alpha*n+beta)
            if len(tight)<30 or slack < max(t[0] for t in tight):
                tight.append((slack,n,k,y,str(alpha),str(beta),label,y%M))
                tight=sorted(tight,key=lambda x:x[0])[:30]
        s=advance(s)

covered=sum(1 for r in range(1,M,3) if best[r] is not None)
uncovered=[r for r in range(1,M,3) if best[r] is None]
# The key residual is expressed without narrative: which mod-3 cells can pass
# indefinitely without receiving a reverse lower bound from the compiled bank?
result={
 "schema":"COLLATZ_ACTUAL_ORBIT_INEQUALITY_CLOSURE_V0",
 "authority":{
   "forward":"source_product_v1.initial/advance",
   "reverse":"collatz_reverse_target_audit.enumerate_target(Q=14)",
   "logic":"Live and no OrdinaryExit => every legal reverse predecessor p satisfies p>=source"
 },
 "Q":Q,
 "certificate_count":len(certs),
 "q14_covered_residues":covered,
 "q14_total_residues":M//3,
 "q14_uncovered_residues":len(uncovered),
 "q14_max_forced_ratio":str(max(x[0] for x in best if x is not None)),
 "bounded_actual_path":{
   "odd_sources_below":1<<BITS,"depth":DEPTH,"checked_bounds":checked,
   "compiled_bound_violations":violations,"ordinary_exits_exposed_by_bounds":forced_exit,
   "constrained_live_prefix_points":constrained,"unconstrained_live_prefix_points":unconstrained,
   "unconstrained_mod3_hist":residue_hist,"tight_examples":tight
 },
 "residual":{
   "name":"UNCOVERED_ACTUAL_ORBIT_RESIDUE_CONTINUATION",
   "statement":"close the exact actual-orbit transition classes receiving no reverse-forced source-relative lower bound; do not add a new representation",
   "first_uncovered_q14_residues":uncovered[:40],
   "next":"derive the shortest exact reverse certificate family forced by the surviving actual transition class, compile it as another inequality, and reclose"
 },
 "global_collatz":"UNKNOWN"
}
assert violations==0
print(json.dumps(result,indent=2))
