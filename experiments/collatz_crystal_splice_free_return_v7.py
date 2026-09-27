#!/usr/bin/env python3
"""Crystal V7: splice-free source-changing first-return macro.

No constructor bank.  The only transition is the V3/V6 canonical owner splice:
walk accelerated odd steps while valuations are 1 or 2; at the first valuation
>=3, replace that high state by its canonical owner.  The owner and the high
state have the same protected future.

On a hypothetical minimal-bad source n every such owner must remain >= n.
This experiment quotients those source-changing macro transitions and asks
whether a small consequence-derived abstraction has an acyclic residual graph,
or exposes an exact recurrent abstract cycle.

Bounded discovery only; a recurrent abstract cycle is an obstruction to the
tested abstraction, not a Collatz counterexample.
"""
from __future__ import annotations
from collections import defaultdict
import json
from fractions import Fraction

LIMIT = 1 << 18
MACRO_CAP = 80

def v2(x: int) -> int:
    return (x & -x).bit_length() - 1

def U(x: int):
    z = 3*x + 1
    s = v2(z)
    return z >> s, s

def shell4(n: int, x: int) -> int:
    if x < n:
        return -1
    h = 0
    y = n
    while 4*y <= x:
        y *= 4
        h += 1
    return h

def macro(x: int):
    """Return canonical owner p at first high valuation and exact affine data.

    p = (A*x+E)/D on this exact low-word/high-owner cylinder.
    """
    cur = x
    word = []
    A, E, D = 1, 0, 1
    for _ in range(10000):
        nxt, s = U(cur)
        if s >= 3:
            k = (s - 1)//2
            pow4 = 1 << (2*k)
            c = (pow4 - 1)//3
            assert (cur-c) % pow4 == 0
            p = (cur-c)//pow4
            assert p > 0 and p & 1
            Ep = E - D*c
            Dp = D*pow4
            assert A*x + Ep == Dp*p
            eps = s - 2*k
            assert eps in (1,2)
            slope = -1 if A < Dp else (1 if A > Dp else 0)
            # Sign of the affine fixed point E/(D-A), if defined.
            den = Dp-A
            fp_sign = 0
            if den:
                q = Fraction(Ep, den)
                fp_sign = -1 if q < 0 else (1 if q > 0 else 0)
            return {
                "p":p, "word":tuple(word), "high_s":s, "owner_depth":k,
                "eps":eps, "A":A, "E":Ep, "D":Dp,
                "slope_class":slope, "fixedpoint_sign":fp_sign,
            }
        # exact low accelerated step
        word.append(s)
        E = 3*E + D
        A = 3*A
        D <<= s
        cur = nxt
    raise AssertionError("low-valuation guard exhausted")

def node_features(n:int, x:int, m:dict, level:int):
    base = (shell4(n,x), x % 3, x % 8)
    if level == 0:
        return base
    if level == 1:
        return base + (m["slope_class"],)
    return base + (m["slope_class"], m["fixedpoint_sign"], m["eps"])

def find_cycle(nodes, succ):
    seen=set(); stack=[]; on=set()
    def dfs(v):
        seen.add(v); stack.append(v); on.add(v)
        for w in sorted(succ.get(v,()), key=repr):
            if w not in nodes: continue
            if w not in seen:
                got=dfs(w)
                if got:return got
            elif w in on:
                i=stack.index(w)
                return stack[i:]+[w]
        stack.pop(); on.remove(v)
        return None
    for v in sorted(nodes,key=repr):
        if v not in seen:
            got=dfs(v)
            if got:return got
    return []

def greatest_kernel(nodes, succ, exits):
    live=set(nodes)-set(exits)
    while True:
        dead={v for v in live if not (set(succ.get(v,())) & live)}
        if not dead:return live
        live-=dead

graphs=[]
for level in range(3):
    succ=defaultdict(set)
    edge_example={}
    exits=set()
    sources_closed=0
    max_macros=0
    record=None

    for n in range(3,LIMIT,2):
        x=n
        for r in range(MACRO_CAP):
            m=macro(x)
            a=node_features(n,x,m,level)
            p=m["p"]
            if p < n:
                exits.add(a)
                sources_closed += 1
                if r+1 > max_macros:
                    max_macros=r+1
                    record={"n":n,"macros":r+1,"x":x,"p":p,
                            "word":"".join(map(str,m["word"])),
                            "owner_depth":m["owner_depth"]}
                break
            m2=macro(p)
            b=node_features(n,p,m2,level)
            succ[a].add(b)
            edge_example.setdefault((a,b),{
                "n":n,"x":x,"p":p,
                "word":"".join(map(str,m["word"])),
                "owner_depth":m["owner_depth"],
                "A":str(m["A"]),"E":str(m["E"]),"D":str(m["D"])
            })
            x=p
        else:
            raise AssertionError(("bounded source not closed",n,MACRO_CAP))

    nodes=set(succ)|set(exits)
    for vs in succ.values():nodes.update(vs)
    ker=greatest_kernel(nodes,succ,exits)
    cyc=find_cycle(ker,succ)
    cyc_edges=[]
    if cyc:
        for a,b in zip(cyc,cyc[1:]):
            cyc_edges.append({"from":repr(a),"to":repr(b),
                              "example":edge_example.get((a,b))})
    graphs.append({
        "level":level,
        "fields": [
            "source_shell4","x_mod3","x_mod8",
            *([] if level==0 else ["macro_slope_class"]),
            *([] if level<2 else ["macro_fixedpoint_sign","normalized_high_epsilon"])
        ],
        "abstract_states":len(nodes),
        "residual_kernel_states":len(ker),
        "has_recurrent_abstract_cycle":bool(cyc),
        "cycle":cyc_edges,
        "bounded_sources_closed":sources_closed,
        "record_macro_wait":max_macros,
        "record":record,
    })

out={
  "schema":"COLLATZ_CRYSTAL_SPLICE_FREE_RETURN_V7",
  "source_limit_exclusive":LIMIT,
  "macro_cap":MACRO_CAP,
  "protected_transition":"first high valuation -> canonical owner with same future",
  "residual_guard":"canonical owner >= original source",
  "graphs":graphs,
  "status":"ABSTRACT_RECURRENT_OBSTRUCTION" if graphs[-1]["has_recurrent_abstract_cycle"]
           else "BOUNDED_EMPTY_ABSTRACT_KERNEL",
  "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
