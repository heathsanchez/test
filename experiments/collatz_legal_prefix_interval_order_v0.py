#!/usr/bin/env python3
"""Test recursive sibling-interval separation in the exact legal first-crossing tree.

For fixed terminal J,q, each legal parity prefix defines a set of canonical
terminal (R,Y) completions. At every branching prefix, ask whether the two
children have disjoint R intervals and disjoint Y intervals in the same order.
If universal, this would prove the legal endpoint order theorem recursively
without requiring dominance comparability.
"""
import json
def terminal_states(J):
    # carry prefix bits as integer and collect full terminals
    states=[(0,0,0,0)] # q,R,Y,bits
    for k in range(J):
        nxt=[]
        for q,R,Y,bits in states:
            for b in (0,1):
                e=b^(Y&1);R2=R+(e<<k);Z=Y+e*3**q
                Y2=Z//2 if b==0 else (3*Z+1)//2
                q2=q+b;w=bits|(b<<k)
                if k+1<J:
                    if 3**q2>=2**(k+1):nxt.append((q2,R2,Y2,w))
                else:
                    if 3**q2<2**J and 3**q2>=2**(J-1):nxt.append((q2,R2,Y2,w))
        states=nxt
    return states
rows=[];first_fail=None
for J in range(2,28):
    terms=terminal_states(J)
    if not terms:continue
    # prefix maps keyed by (length,prefix low bits), values terminal R,Y
    ok=True;checked=0;fail=None
    for l in range(J):
        groups={}
        mask=(1<<l)-1
        for q,R,Y,w in terms:
            p=w&mask
            b=(w>>l)&1
            groups.setdefault((p,b),[]).append((R,Y,w))
        parents={p for p,b in groups if (p,1-b) in groups}
        for p in parents:
            if (p,0) not in groups or (p,1) not in groups:continue
            A=groups[(p,0)];B=groups[(p,1)]
            rA=(min(x[0] for x in A),max(x[0] for x in A))
            rB=(min(x[0] for x in B),max(x[0] for x in B))
            yA=(min(x[1] for x in A),max(x[1] for x in A))
            yB=(min(x[1] for x in B),max(x[1] for x in B))
            rord=-1 if rA[1]<rB[0] else (1 if rB[1]<rA[0] else 0)
            yord=-1 if yA[1]<yB[0] else (1 if yB[1]<yA[0] else 0)
            checked+=1
            if rord==0 or yord==0 or rord!=yord:
                ok=False;fail={"prefix_len":l,"prefix":p,"R0":rA,"R1":rB,"Y0":yA,"Y1":yB,"rord":rord,"yord":yord};break
        if not ok:break
    if not ok and first_fail is None:first_fail={"J":J,**fail}
    rows.append({"J":J,"legal":len(terms),"branch_nodes_checked":checked,"separated":ok})
result={
 "schema":"COLLATZ_LEGAL_PREFIX_INTERVAL_ORDER_V0",
 "j_max":27,"all_separated":all(r["separated"] for r in rows),
 "first_failure":first_fail,"rows":rows,
 "candidate_if_green":"recursive sibling interval separation => global R/Y order => minimum-R maximizes M",
 "next":"prove recursive interval bounds if green; if red, retain first overlap as exact obstruction and refine the state minimally",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
