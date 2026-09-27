#!/usr/bin/env python3
"""Crystal residual cycle: source-coupled equality escape.

This experiment acts only on exact canonical source cylinders (q,R,Y).  It
does not promote aggregate (j,m) count transitions to source transitions.

Goal: discover/falsify the candidate local theorem
  equality macro step => next macro step is strict or exits.
Any repeated equality is retained as an exact counterexample residual.
Finite success remains bounded evidence, never a universal Collatz claim.
"""
from __future__ import annotations
import json
from collections import defaultdict
from fractions import Fraction

DEPTH=22
BMAX=8

def qmin(depth):
    out=[0]*(depth+1); q=0; p=1
    for j in range(1,depth+1):
        while p < (1<<j): p*=3; q+=1
        out[j]=q
    return out

QM=qmin(DEPTH)

def children(s,j):
    q,R,Y=s
    out=[]
    for bit in (0,1):
        lift=(bit-Y)&1
        Rp=R+(lift<<(j-1)); z=Y+(3**q)*lift
        Yp=(3*z+1)//2 if bit else z//2
        qp=q+bit
        if qp>=QM[j]: out.append((qp,Rp,Yp))
    return out

levels=[[(0,0,0)]]
parents=[{}]
for j in range(1,DEPTH+1):
    nx=[]; par={}
    for s in levels[-1]:
        for t in children(s,j):
            nx.append(t); par[t]=s
    levels.append(nx); parents.append(par)

# Source-coupled observable: exact cylinder resource, not population count.
# The affine endpoint Y/R is the concrete source-normalized displacement;
# R=0 is the distinguished zero source and is excluded from theorem discovery.
def resource(s):
    q,R,Y=s
    return None if R==0 else Fraction(Y,R)

def jump_from_state(s,j,b):
    frontier=[s]
    for k in range(j+1,j+b+1):
        nxt=[]
        for u in frontier:nxt.extend(children(u,k))
        frontier=nxt
        if not frontier:return ()
    return tuple(frontier)

# A macro action is warranted nonexpansive only if EVERY exact descendant
# cylinder after b steps has resource <= the source state's resource.
def ratio_kind(s,j,b):
    r0=resource(s)
    if r0 is None:return None,()
    ts=jump_from_state(s,j,b)
    if not ts:return "EXIT",()
    vals=[resource(t) for t in ts if resource(t) is not None]
    if len(vals)!=len(ts):return None,ts
    mx=max(vals)
    if mx<r0:return "STRICT",ts
    if mx==r0:return "EQUAL",ts
    return "EXPAND",ts

# Crystal: coarsest earned role first.  A role is (parity,q-excess); split by
# exact low source/carry bits only when conflicting protected consequences occur.
def coarse_role(s,j):
    q,R,Y=s
    return (j&1,q-QM[j])

def outcome_signature(s,j,b):
    kind,ts=ratio_kind(s,j,b)
    return kind

states=[(j,s) for j in range(1,DEPTH-BMAX*2+1) for s in levels[j] if s[1]]
roles=defaultdict(list)
for j,s in states:roles[coarse_role(s,j)].append((j,s))

cycles=[]; splits={}; policies={}
for role,xs in sorted(roles.items(),key=repr):
    chosen=None
    for b in range(1,BMAX+1):
        outs=[outcome_signature(s,j,b) for j,s in xs]
        if outs and all(o in ("STRICT","EQUAL","EXIT") for o in outs):
            chosen=b; break
    if chosen is not None: policies[role]=chosen
cycles.append({"cycle":1,"action":"coarsest-source-coupled-policy",
 "roles":len(roles),"policy_roles":len(policies),
 "residual":"roles without a common exact nonexpansive macro action"})

# SPLIT only conflicting roles, using minimum low-bit width that makes observed
# protected outcomes deterministic for the chosen action.
for role,b in policies.items():
    xs=roles[role]
    outs={(j,s):outcome_signature(s,j,b) for j,s in xs}
    if len(set(outs.values()))<=1:continue
    for w in range(1,13):
        g=defaultdict(set)
        for j,s in xs:
            q,R,Y=s; mask=(1<<w)-1
            g[(R&mask,Y&mask)].add(outs[(j,s)])
        if all(len(v)==1 for v in g.values()):
            splits[role]=w; break
cycles.append({"cycle":2,"action":"separator-driven-split",
 "conflicting_roles":sum(1 for role,b in policies.items() if len({outcome_signature(s,j,b) for j,s in roles[role]})>1),
 "resolved_by_minimum_low_bits":len(splits),"splits":{repr(k):v for k,v in splits.items()}})

# Theorem falsification: for every exact equality edge under the warranted
# policy, inspect each ACTUAL descendant and require its own next warranted
# macro action to be strict/exit.  Missing policy is UNKNOWN, not success.
eq=0; strict_or_exit=0; counter=[]; unknown=[]
for role,b in policies.items():
    for j,s in roles[role]:
        kind,ts=ratio_kind(s,j,b)
        if kind!="EQUAL":continue
        eq+=1
        for t in ts:
            j2=j+b
            role2=coarse_role(t,j2)
            b2=policies.get(role2)
            if b2 is None:
                unknown.append({"j":j,"source":s,"after":t,"reason":"no_next_policy"});continue
            k2,_=ratio_kind(t,j2,b2)
            if k2 in ("STRICT","EXIT"):strict_or_exit+=1
            elif k2=="EQUAL":
                counter.append({"j":j,"source":s,"b":b,"after":t,"next_b":b2})
            else:
                unknown.append({"j":j,"source":s,"after":t,"reason":k2})
cycles.append({"cycle":3,"action":"actual-descendant-equality-escape",
 "equality_edges":eq,"strict_or_exit_descendants":strict_or_exit,
 "repeated_equality_counterexamples":len(counter),"unknown":len(unknown),
 "first_counterexamples":counter[:20],"first_unknown":unknown[:20]})

if counter:
    status="CANDIDATE_REJECTED"
    residual={"name":"REPEATED_SOURCE_EQUALITY","examples":counter[:20],
      "next":"refine only the conflicting source/carry distinction exposed by these exact paths"}
elif unknown:
    status="UNKNOWN"
    residual={"name":"NEXT_POLICY_GAP","examples":unknown[:20],
      "next":"acquire the minimum exact next-policy capability on these source-coupled paths"}
else:
    status="BOUNDED_EQUALITY_ESCAPE"
    residual={"name":"ALL_DEPTH_GENERALIZATION",
      "next":"derive the finite separator/policy law symbolically for arbitrary depth; bounded success is not universal"}

result={"schema":"COLLATZ_CRYSTAL_SOURCE_EQUALITY_ESCAPE_V1","depth":DEPTH,"bmax":BMAX,
 "exact_live_states":sum(len(x) for x in levels),"cycles":cycles,"status":status,
 "residual":residual,"global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2,default=str))
