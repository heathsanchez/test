#!/usr/bin/env python3
"""Crystal full-affine hard-crossing join.

For a hard q<n crossing write y=n+g with 3g<q<n.
A reverse cert p=(a*y-c)/d is below n iff a*g < (d-a)*n+c.
We ask which certs are guaranteed solely by the universal hard-crossing
inequalities, using q only via g <= floor((n-1)/3). This is an exact
symbolic sufficient test, not a sampled source test.
"""
import json
import collatz_reverse_predecessor_tree as pred
rows=[]
for Q in range(1,15):
    cs=pred.enumerate_first_contractions(Q); M=3**Q
    killed=bytearray(M); selected=[]
    for c in cs:
        # worst universal g under 3g<q<n is g <= floor((n-2)/3).
        # Need a*floor((n-2)/3) < (d-a)n+c for every n>=2.
        # Multiply by 3 and use floor upper bound: sufficient exact linear law
        # a*(n-2) < 3*(d-a)*n + 3c.
        # coefficient comparison; if RHS-LHS has nonnegative n coefficient,
        # check smallest n=2. If negative, no universal all-n guarantee.
        coef=3*(c.d-c.a)-c.a
        const=3*c.c+2*c.a
        universal = coef>=0 and (2*coef+const)>0
        if not universal: continue
        add=0
        for r in range(c.residue,M,c.d):
            if r%3!=1: continue
            if not killed[r]: killed[r]=1;add+=1
        if add:selected.append({"word":c.word,"mod":c.d,"residue":c.residue,
          "a":c.a,"c":c.c,"added":add})
    universe=[r for r in range(1,M,3)]
    live=[r for r in universe if not killed[r]]
    rows.append({"Q":Q,"universe":len(universe),"killed":len(universe)-len(live),
                 "live":len(live),"first_live":live[:30],"selected_count":len(selected),
                 "selected":selected[:30]})
print(json.dumps({"schema":"COLLATZ_CRYSTAL_FULL_AFFINE_HARD_CROSSING_JOIN_V0",
 "premise":"q<n and 3*(y-n)<q, hence g=y-n <= floor((n-2)/3)",
 "certificate":"p=(a*y-c)/d<n iff a*g<(d-a)*n+c",
 "rows":rows,"global_collatz":"UNKNOWN"},indent=2))
