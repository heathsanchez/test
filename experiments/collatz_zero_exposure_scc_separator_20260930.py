#!/usr/bin/env python3
from fractions import Fraction
import json, hashlib
import collatz_zero_exposure_independent_grammar_20260930 as g

_, zero, runs, _ = g.collect(8193,32767)
edges={(e["old_law"],e["new_law"]) for e in zero}
nodes={x for e in edges for x in e}
sccs=g.tarjan(nodes,edges)
sccs=[c for c in sccs if len(c)>1 or (len(c)==1 and (c[0],c[0]) in edges)]
assert len(sccs)==1 and len(sccs[0])==2
a,b=sccs[0]
assert (a,b) in edges and (b,a) in edges

def compose(x,y):
    _,A1,B1,P1,D1=x
    _,A2,B2,P2,D2=y
    return A2*A1, A2*B1+B2*P1, P2*P1, D1+D2

def fp(comp):
    A,B,P,D=comp
    C=P-A
    if C==0:return None
    q=Fraction(B,C)
    return {"num":q.numerator,"den":q.denominator,
            "positive_integer":q.denominator==1 and q.numerator>0}

ab=compose(a,b);ba=compose(b,a)
qab=fp(ab);qba=fp(ba)
occ_ab=[e for e in zero if e["old_law"]==a and e["new_law"]==b]
occ_ba=[e for e in zero if e["old_law"]==b and e["new_law"]==a]
sab=sorted(set(e["source"] for e in occ_ab))
sba=sorted(set(e["source"] for e in occ_ba))
common=sorted(set(sab)&set(sba))
cycles=[]
for rr in runs:
    laws=[rr[0]["old_law"]]+[e["new_law"] for e in rr]
    for i in range(len(laws)-2):
        if laws[i]==laws[i+2] and {laws[i],laws[i+1]}=={a,b}:
            cycles.append({"source":rr[i]["source"],"anchor":rr[i]["anchor"],
                           "laws":[laws[i],laws[i+1],laws[i+2]]})
result={
 "schema":"COLLATZ_ZERO_EXPOSURE_SCC_SEPARATOR_20260930",
 "scc":[a,b],
 "edge_occurrences":{"a_to_b":len(occ_ab),"b_to_a":len(occ_ba),
                     "sources_a_to_b":sab,"sources_b_to_a":sba,
                     "common_sources":common},
 "concrete_zero_cycle_runs":cycles,
 "compose_a_then_b":{"A":ab[0],"B":ab[1],"P":ab[2],"D":ab[3],"fixed_point":qab},
 "compose_b_then_a":{"A":ba[0],"B":ba[1],"P":ba[2],"D":ba[3],"fixed_point":qba},
 "verdict":"SCC_KILLED_BY_NONINTEGRAL_COMPOSITE_FIXED_POINT"
   if qab and qba and not qab["positive_integer"] and not qba["positive_integer"]
   else "SCC_REQUIRES_FURTHER_AUDIT",
 "global_collatz":"UNKNOWN"}
result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True,default=str))
