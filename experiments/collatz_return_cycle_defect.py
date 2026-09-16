#!/usr/bin/env python3
"""Exact defect countdown on repeated return-cycle signatures.

On a stabilized odd-episode tail, loop-erasure produces exact return cycles.
For one return word W from an r-state back to the same r-state,

    F_W(m) = (A m + B) / 2^D.

Let C=2^D-A and define the integer fixed-point defect

    Delta_W(m) = C*m - B.

Because A is odd,

    Delta_W(F_W(m)) = A*Delta_W(m)/2^D,

so every exact traversal with Delta != 0 reduces v2(|Delta|) by exactly D.

A fixed word therefore cannot repeat consecutively forever unless Delta=0.
This experiment tests a stronger candidate needed for varying stable tails:

    whenever the SAME exact return-cycle signature reappears later
    (possibly after other return cycles), its start-defect valuation is
    strictly smaller than on the previous occurrence.

If true universally for a finite signature set, this would give a common
countdown across varying cycles.  A single equal/increasing repeat falsifies
that candidate and is reported explicitly.

The census is exact on bounded ordinary integers and separately on the known
H512 boundary core.  It is a falsification/profiling experiment, not a global
Collatz proof.
"""

from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

from collatz_odd_episode_grammar import episode

BOUNDARY_CORE=26130934783


def v2(n:int)->int:
    assert n
    n=abs(n)
    return (n & -n).bit_length()-1


def compose_word(word):
    A,B,D=1,0,0
    for r,s,rp in word:
        d=s+rp
        B=(3**r)*B + ((1<<s)-1)*(1<<D)
        A=(3**r)*A
        D+=d
    return A,B,D


def rho(A:int,B:int,D:int):
    mod=1<<(D+1)
    return ((1<<D)-B)*pow(A,-1,mod)%mod,mod


def stable_trace(x0:int,cap:int):
    """Return stabilized states/branches up to first descent below x0."""
    r0=(x0+1 & -(x0+1)).bit_length()-1
    m0=(x0+1)>>r0

    x=x0
    A,B,D=1,0,0
    stable_start_state=None
    states=[]      # (r,m,x)
    branches=[]    # (r,s,rp), branch i maps state i -> i+1
    descended=False

    # Build the whole trace first, remembering the first state AFTER an exact
    # pullback prefix whose canonical residue has stabilized to m0.
    raw_states=[]
    raw_branches=[]
    raw_states.append((r0,m0,x0))

    for j in range(cap):
        r,m,s,rp,mp,xp=episode(x)
        assert raw_states[-1][:2]==(r,m)
        raw_branches.append((r,s,rp))
        raw_states.append((rp,mp,xp))

        d=s+rp
        B=(3**r)*B + ((1<<s)-1)*(1<<D)
        A=(3**r)*A
        D+=d
        rr,mod=rho(A,B,D)
        assert m0%mod==rr
        assert (A*m0+B)==(1<<D)*mp

        if stable_start_state is None and mod>m0:
            assert rr==m0
            stable_start_state=j+1

        if xp<x0:
            descended=True
            break
        x=xp

    if stable_start_state is None:
        return {
            "stable":False,"descended":descended,
            "states":[],"branches":[],
        }

    states=raw_states[stable_start_state:]
    branches=raw_branches[stable_start_state:]
    # If descent happened on the very branch that created stable_start_state,
    # there are no stable branches to analyze; states still has one state.
    if len(branches)+1>len(states):
        branches=branches[:max(0,len(states)-1)]

    return {
        "stable":True,"descended":descended,
        "states":states,"branches":branches,
    }


def analyze_cycles(states,branches):
    if not states:
        return {
            "cycles":0,"unique_signatures":0,"signature_repeats":0,
            "repeat_decrease":0,"repeat_equal":0,"repeat_increase":0,
            "first_bad":None,"fixed_defect_zero":0,
            "max_defect_v2":0,"max_D":0,
        }

    # Spine entries are (r, state_index).  On a return, replace the old state
    # by the current state at the same r and erase the intervening spine.
    spine=[(states[0][0],0)]
    last_defect={}
    cycles=0
    signatures=set()
    sig_repeats=dec=eq=inc=0
    first_bad=None
    fixed_zero=0
    max_v=0
    max_D=0

    for j,b in enumerate(branches):
        if j+1>=len(states):
            break
        rp=states[j+1][0]
        pos=None
        for i,(rr,idx) in enumerate(spine):
            if rr==rp:
                pos=i
                break

        if pos is None:
            spine.append((rp,j+1))
            continue

        start_idx=spine[pos][1]
        word=tuple(branches[start_idx:j+1])
        assert word and word[0][0]==rp and word[-1][2]==rp
        A,B,D=compose_word(word)
        m_start=states[start_idx][1]
        m_end=states[j+1][1]
        assert (A*m_start+B)==(1<<D)*m_end

        C=(1<<D)-A
        delta=C*m_start-B
        delta_end=C*m_end-B
        assert (1<<D)*delta_end==A*delta

        signature=word
        signatures.add(signature)
        cycles+=1
        max_D=max(max_D,D)

        if delta==0:
            fixed_zero+=1
            dv=None
        else:
            dv=v2(delta)
            assert dv>=D,(word,m_start,D,dv)
            assert v2(delta_end)==dv-D
            max_v=max(max_v,dv)

        if signature in last_defect and dv is not None:
            prev=last_defect[signature]
            sig_repeats+=1
            if dv<prev:
                dec+=1;kind="decrease"
            elif dv==prev:
                eq+=1;kind="equal"
            else:
                inc+=1;kind="increase"
            if kind!="decrease" and first_bad is None:
                first_bad={
                    "kind":kind,
                    "signature":[list(z) for z in signature],
                    "previous_defect_v2":prev,
                    "current_defect_v2":dv,
                    "cycle_start_state_index":start_idx,
                    "cycle_end_state_index":j+1,
                    "m_start":m_start,
                    "m_end":m_end,
                    "A":A,"B":B,"D":D,
                }
        if dv is not None:
            last_defect[signature]=dv

        # Replace same-r spine node by the current occurrence and erase loop.
        spine=spine[:pos+1]
        spine[pos]=(rp,j+1)

    return {
        "cycles":cycles,
        "unique_signatures":len(signatures),
        "signature_repeats":sig_repeats,
        "repeat_decrease":dec,
        "repeat_equal":eq,
        "repeat_increase":inc,
        "first_bad":first_bad,
        "fixed_defect_zero":fixed_zero,
        "max_defect_v2":max_v,
        "max_D":max_D,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=12)
    ap.add_argument("--precision",type=int,default=14)
    ap.add_argument("--cap",type=int,default=384)
    ap.add_argument("--out")
    a=ap.parse_args()

    M=1<<a.precision
    totals=Counter()
    first_bad=None
    bad_seed=None
    cases=stable_cases=unresolved=0

    for r0 in range(1,a.max_r+1):
        for m0 in range(1,M,2):
            x0=(1<<r0)*m0-1
            if x0==1:
                continue
            cases+=1
            tr=stable_trace(x0,a.cap)
            if not tr["descended"]:
                unresolved+=1
            if not tr["stable"]:
                continue
            stable_cases+=1
            z=analyze_cycles(tr["states"],tr["branches"])
            for k in (
                "cycles","unique_signatures","signature_repeats",
                "repeat_decrease","repeat_equal","repeat_increase",
                "fixed_defect_zero"
            ):
                totals[k]+=z[k]
            totals["max_defect_v2"]=max(totals["max_defect_v2"],z["max_defect_v2"])
            totals["max_D"]=max(totals["max_D"],z["max_D"])
            if z["first_bad"] is not None and first_bad is None:
                first_bad=z["first_bad"];bad_seed=x0

    core_trace=stable_trace(BOUNDARY_CORE,2048)
    core=analyze_cycles(core_trace["states"],core_trace["branches"])

    out={
        "kind":"return_cycle_defect_countdown",
        "max_r":a.max_r,"precision":a.precision,"cap":a.cap,
        "cases":cases,"stable_cases":stable_cases,"unresolved":unresolved,
        **dict(totals),
        "candidate_repeated_signature_defect_strictly_decreases":(
            totals["repeat_equal"]==0 and totals["repeat_increase"]==0
        ),
        "first_bad_seed":bad_seed,
        "first_bad":first_bad,
        "boundary_core":{
            "seed":BOUNDARY_CORE,
            "descended":core_trace["descended"],
            **core,
        },
        "proof_status":"bounded exact test of varying-cycle defect candidate; not global proof",
    }

    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("RETURN_CYCLE_DEFECT_COUNTDOWN",
          f"max_r={a.max_r}",f"precision={a.precision}",
          f"cases={cases}",f"stable_cases={stable_cases}",
          f"cycles={totals['cycles']}",
          f"signature_repeats={totals['signature_repeats']}",
          f"repeat_decrease={totals['repeat_decrease']}",
          f"repeat_equal={totals['repeat_equal']}",
          f"repeat_increase={totals['repeat_increase']}",
          f"fixed_zero={totals['fixed_defect_zero']}",
          f"unresolved={unresolved}")
    if first_bad is not None:
        print("RETURN_CYCLE_DEFECT_COUNTEREXAMPLE",
              f"seed={bad_seed}",
              json.dumps(first_bad,separators=(",",":")))
    print("BOUNDARY_CORE_RETURN_DEFECT",
          f"cycles={core['cycles']}",
          f"repeats={core['signature_repeats']}",
          f"decrease={core['repeat_decrease']}",
          f"equal={core['repeat_equal']}",
          f"increase={core['repeat_increase']}",
          f"fixed_zero={core['fixed_defect_zero']}")
    if out["candidate_repeated_signature_defect_strictly_decreases"]:
        print("BOUNDED_TEST_SUPPORTS_REPEATED_SIGNATURE_DEFECT_DESCENT")
    else:
        print("REPEATED_SIGNATURE_DEFECT_DESCENT_CANDIDATE_FALSIFIED")
    print("VERIFIED_RETURN_CYCLE_DEFECT_CENSUS")


if __name__=="__main__":
    main()
