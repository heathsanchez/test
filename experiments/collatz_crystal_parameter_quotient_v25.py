#!/usr/bin/env python3
"""Crystal V25: exact parameter-halving quotient scout for the sole V23 cell.

Authority parent:
  collatz-crystal-affine-family-v24@8401a07d8bb5b78455eb365467c6d6610e33dea9

This does not enumerate a larger ordinary-source interval.  It refines only the
one exact V23 affine family
  n(t)=N0+NC*t
by the forced parameter bit t=2u+b.

For each reachable parameter cell t=r+2^d*u:
* derive its maximal fixed shortcut prefix exactly;
* attach any uniform direct descent or quarter-splice exit on that prefix;
* at the maximal affine interface, exhaust every uniform reverse E/O word whose
  slope can still become no larger than the cell's source slope, looking for an
  exact lower-source common-future witness;
* otherwise split only on the next parameter bit.

The finite tree is theorem-discovery evidence, not a global Collatz proof.
A separate zero-tail control follows b=0 after the frozen frontier, because a
natural parameter has an eventually-zero binary tail.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from functools import lru_cache
import json

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
ROOT_ENDPOINT = 91_182_490_942_926_966_077
ROOT_SLOPE = 3**46

TREE_DEPTH = 9
ZERO_TAIL_EXTRA = 160

def v2(x:int)->int:
    return (x & -x).bit_length()-1

def v3(x:int)->int:
    k=0
    while x and x%3==0:
        x//=3; k+=1
    return k

def is_pow3(x:int):
    if x<=0:return None
    k=0
    while x%3==0:
        x//=3;k+=1
    return k if x==1 else None

def fixed_prefix(N:int,S:int):
    """Return (j,A,C,q) through the first depth with odd affine slope."""
    out=[]
    A,C=N,S
    q=0;j=0
    while True:
        out.append((j,A,C,q))
        if C&1:
            break
        odd=A&1
        if odd:
            A=(3*A+1)//2
            C=3*C//2
            q+=1
        else:
            A//=2
            C//=2
        j+=1
    return out

def direct_or_splice(prefix,N,S):
    for j,A,C,q in prefix:
        # Strict uniform A+C*u < N+S*u for every u>=0.
        if ((A < N and C <= S) or (A <= N and C < S)):
            return {"kind":"D","depth":j,"endpoint0":A,"endpointSlope":C}
        # Uniform quarter splice needs mod-8 fixed across the whole cell.
        if C%8==0 and A%8==5 and A<=4*N and C<=4*S:
            return {"kind":"S","depth":j,"endpoint0":A,"endpointSlope":C}
    return None

def reverse_lower_witness(A:int,C:int,N:int,S:int):
    """Exact dynamic search at an odd-slope affine interface.

    Reverse E: z <- 2z.
    Reverse O: z <- (2z-1)/3 when uniform divisibility permits.

    At the maximal fixed interface C is exactly a power of 3.  Parameterize a
    reverse word by its number o of O operations and total E operations before
    each O.  Slope bounds make the search finite.  Trailing E after the final O
    cannot create a lower source, so omitting it is sound.
    """
    m=is_pow3(C)
    assert m is not None

    maxE={}
    globalE=-1
    for o in range(m+1):
        e=-1
        for z in range(0,512):
            if C*(1 << (z+o)) <= S*(3**o):
                e=z
            else:
                break
        maxE[o]=e
        globalE=max(globalE,e)
    if globalE < 0:
        return None,0

    # dp[E] maps current constants to one exact witnessing reverse word.
    dp={0:{A:""}}
    states=1
    for o in range(m):
        nxt=defaultdict(dict)
        o2=o+1
        for E,cmap in dp.items():
            for a,w in cmap.items():
                if a%3==0:
                    continue
                # Need 2^e*a == 2 mod 3 before the next O.
                parity=0 if a%3==2 else 1
                for e in range(parity,globalE-E+1,2):
                    E2=E+e
                    ae=a<<e
                    coeff_before=C*(1 << (E2+o))//(3**o)
                    if ae%3!=2 or coeff_before%3:
                        continue
                    na=(2*ae-1)//3
                    nc=(2*coeff_before)//3
                    nw=w+("E"*e)+"O"
                    states+=1

                    if na>0 and ((na<N and nc<=S) or (na<=N and nc<S)):
                        return {
                            "word":nw,
                            "p0":na,
                            "pSlope":nc,
                            "oddInverse":o2,
                            "evenLifts":E2,
                        },states

                    # Even if every remaining 3-adic factor is spent on O,
                    # the slope cannot fall below this exact lower envelope.
                    rem=m-o2
                    if nc*(2**rem) > S*(3**rem):
                        continue
                    if na not in nxt[E2]:
                        nxt[E2][na]=nw
        dp=dict(nxt)
        if not dp:
            break
    return None,states

@lru_cache(maxsize=None)
def classify_cell(d:int,r:int,with_merge:bool=True):
    N=N0+NC*r
    S=NC*(1<<d)
    pref=fixed_prefix(N,S)
    assert pref[-1][0]==59+d
    exit0=direct_or_splice(pref,N,S)
    if exit0 is not None:
        return {"terminal":True,"exit":exit0,"reverseStates":0}
    A,C=pref[-1][1],pref[-1][2]
    assert is_pow3(C) is not None
    if with_merge:
        w,states=reverse_lower_witness(A,C,N,S)
        if w is not None:
            return {
                "terminal":True,
                "exit":{"kind":"M","depth":59+d,"reverse":w},
                "reverseStates":states,
            }
    else:
        states=0
    return {
        "terminal":False,
        "interface":{"depth":59+d,"A":A,"C":C,"q":pref[-1][3]},
        "reverseStates":states,
    }

def main():
    # Recheck V24 root affine interface independently.
    root=fixed_prefix(N0,NC)
    assert root[-1][0]==59
    assert root[-1][1]==ROOT_ENDPOINT
    assert root[-1][2]==ROOT_SLOPE
    assert root[-1][3]==38

    frontier=[0]
    levels=[]
    transitions=[]
    totals=Counter()
    total_reverse=0
    final_survivors=[]

    for d in range(TREE_DEPTH+1):
        next_frontier=[]
        exits=Counter()
        survivors=[]
        level_reverse=0
        for r in frontier:
            z=classify_cell(d,r,with_merge=True)
            level_reverse+=z["reverseStates"]
            total_reverse+=z["reverseStates"]
            if z["terminal"]:
                k=z["exit"]["kind"]
                exits[k]+=1
                totals["exit_"+k]+=1
            else:
                survivors.append(r)
                if d<TREE_DEPTH:
                    c0=r
                    c1=r+(1<<d)
                    transitions.append({"depth":d,"r":r,"bit":0,"child":c0})
                    transitions.append({"depth":d,"r":r,"bit":1,"child":c1})
                    next_frontier.extend((c0,c1))

        levels.append({
            "depth":d,
            "input_cells":len(frontier),
            "exits":dict(sorted(exits.items())),
            "survivors":len(survivors),
            "first_survivors":survivors[:64],
            "reverse_states":level_reverse,
        })
        if d==TREE_DEPTH:
            final_survivors=survivors
            break
        frontier=next_frontier

    # Natural-source control.  A natural t has an eventually-zero bit tail.
    # For every frontier survivor, hold r fixed and append only zero bits.
    # We deliberately use only direct/splice here: a positive result is a
    # certificate without depending on another reverse-search heuristic.
    zero_tail=[]
    zero_unclosed=[]
    max_wait=-1
    for r in final_survivors:
        hit=None
        for e in range(ZERO_TAIL_EXTRA+1):
            d=TREE_DEPTH+e
            z=classify_cell(d,r,with_merge=False)
            if z["terminal"]:
                hit={"extra_zero_bits":e,"depth":d,"exit":z["exit"]}
                max_wait=max(max_wait,e)
                break
        if hit is None:
            zero_unclosed.append(r)
        zero_tail.append({"r":r,"hit":hit})

    # Bit-transition census on the exact nonterminal tree.
    child_status=Counter()
    for d in range(TREE_DEPTH):
        surv=set(levels[d]["first_survivors"]) if levels[d]["survivors"]<=64 else None
        # Full survivor lists are not stored for large levels; recompute only
        # exact child terminal status for each transition source.
    # Reconstruct branching statistics without relying on truncated display.
    frontier=[0]
    branch_rows=[]
    for d in range(TREE_DEPTH):
        nxt=[]
        both=one=none=0
        for r in frontier:
            z=classify_cell(d,r,with_merge=True)
            if z["terminal"]:
                continue
            sts=[]
            for bit,child in ((0,r),(1,r+(1<<d))):
                cz=classify_cell(d+1,child,with_merge=True)
                sts.append(not cz["terminal"])
                if not cz["terminal"]:
                    nxt.append(child)
            if sts==[True,True]: both+=1
            elif sts[0] or sts[1]: one+=1
            else:none+=1
        branch_rows.append({"depth":d,"both_survive":both,"one_survives":one,"no_child_survives":none})
        frontier=nxt

    result={
        "schema":"COLLATZ_CRYSTAL_PARAMETER_QUOTIENT_V25",
        "parent":"collatz-crystal-affine-family-v24@8401a07d8bb5b78455eb365467c6d6610e33dea9",
        "family":{"N0":N0,"NC":NC},
        "tree_depth":TREE_DEPTH,
        "levels":levels,
        "branching":branch_rows,
        "total_reverse_states":total_reverse,
        "frontier_survivors":len(final_survivors),
        "frontier_first":final_survivors[:128],
        "zero_tail_control":{
            "extra_zero_bits":ZERO_TAIL_EXTRA,
            "unclosed":len(zero_unclosed),
            "unclosed_residues":zero_unclosed[:128],
            "max_wait_to_uniform_direct_or_splice":max_wait,
            "first_rows":zero_tail[:64],
        },
        "interpretation":(
            "Exact forced t-bit refinement with fail-closed constructor exits. "
            "The finite raw tree itself cannot certify a universal SCC theorem; "
            "the zero-tail control tests the natural-parameter hazard separately."
        ),
        "promotion_rule":(
            "QED requires a depth-independent right-congruent quotient/rank or "
            "cycle certificate. Finite frontier exhaustion alone is non-evidence."
        ),
        "universal_status":"UNKNOWN",
        "global_collatz":"UNKNOWN",
    }
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
