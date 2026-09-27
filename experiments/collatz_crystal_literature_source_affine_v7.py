#!/usr/bin/env python3
"""Crystal V7: exact source-affine residual compiler joined to literature.

Goal: test whether the currently WARRANTED local source-order constructors,
augmented by LaDue's exact consecutive-source synchronization criterion,
already empty the all-lift 2-adic cylinder residual.

For an odd source cylinder n = R + 2^D z, the first D shortcut parities are
fixed.  Hence every depth-j endpoint has the exact affine form

    T^j(n) = Y_j + 3^q_j 2^(D-j) z.

We intersect exact integer constraints on z >= 0 required by a hypothetical
minimal positive bad source:
  * no direct descent T^j(n) < n;
  * every fixed high-valuation owner lift obeys the Lean-green source barrier
        T^j(n) >= ownerLift_k(n);
  * optional literature splice: if LaDue's same-parity criterion is already
    fixed by the source cylinder, n synchronizes with n-1 and the cylinder is
    impossible for a minimal bad source.

This is a finite-prefix exact compiler, not a Collatz proof.  In particular,
an unbounded z interval is a 2-adic/source-lift survivor, not an ordinary
integer surviving all depths.
"""
from __future__ import annotations
import json, math

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

def v2(x:int)->int:
    assert x>0
    s=0
    while x%2==0:
        s+=1; x//=2
    return s

def add_ge(lo:int, hi:int|None, a:int, b:int):
    """Intersect a*z+b >= 0 with integer z in [lo,hi]."""
    if a==0:
        return lo,hi,b>=0
    if a>0:
        if b<0:
            lo=max(lo,(-b+a-1)//a)
    else:
        d=-a
        if b<0:
            return lo,hi,False
        u=b//d
        hi=u if hi is None else min(hi,u)
    return lo,hi,(hi is None or lo<=hi)

def ladue_lower_sync_fixed(R:int,D:int)->bool:
    """LaDue Thm 4.1 criterion fixed on the whole source cylinder.

    For odd m, m+1 = 2^p(2q+1).  The consecutive starts m-1,m synchronize
    exactly in the same-parity branch p == q (mod 2).  The condition is fixed
    by R mod 2^D once p <= D-2.
    """
    p=v2(R+1)
    if p>D-2:
        return False
    oddcore=(R+1)>>p
    q_parity=((oddcore-1)//2)&1
    return (p&1)==q_parity

def compile_cylinder(D:int,R:int,use_ladue:bool):
    M=1<<D
    lo=1 if R==1 else 0  # exclude n=1 itself
    hi=None
    if use_ladue and ladue_lower_sync_fixed(R,D):
        return None,"ladue"

    y=R; q=0
    monks_hits=0
    owner_events=0
    for j in range(D+1):
        if j:
            if y&1: q+=1
            y=T(y)

        C=(3**q)*(1<<(D-j))  # T^j(R+Mz)=y+Cz

        if j and (y&1) and (y&7) in (1,5):
            monks_hits+=1

        # A minimal bad source never directly descends.
        if j:
            lo,hi,ok=add_ge(lo,hi,C-M,y-R)
            if not ok:
                return None,"descent"

        # Lean-green all-depth owner barrier.  The valuation is fixed on the
        # whole cylinder whenever s < D-j.
        if j<D and (y&1):
            s=v2(3*y+1)
            if 3<=s<D-j:
                k=(s-1)//2
                pow4=4**k
                c=(pow4-1)//3
                # no lower owner means y+Cz >= ownerLift_k(R+Mz)
                lo,hi,ok=add_ge(
                    lo,hi,
                    C-pow4*M,
                    y-pow4*R-c,
                )
                owner_events+=1
                if not ok:
                    return None,"owner"

    return {
        "lo":lo,"hi":hi,"monks_hits":monks_hits,"owner_events":owner_events
    },"survive"

def row(D:int,use_ladue:bool):
    counts={"ladue":0,"descent":0,"owner":0,"survive":0}
    unbounded=bounded=0
    first=[]
    no_monks_hit=0
    owner_event_total=0
    for R in range(1,1<<D,2):
        out,reason=compile_cylinder(D,R,use_ladue)
        counts[reason]+=1
        if out is None: continue
        owner_event_total+=out["owner_events"]
        if out["monks_hits"]==0: no_monks_hit+=1
        if out["hi"] is None: unbounded+=1
        else: bounded+=1
        if len(first)<20:
            first.append({"R":R,**out})
    total=1<<(D-1)
    return {
        "D":D,
        "odd_source_cylinders":total,
        "eliminated_ladue":counts["ladue"],
        "eliminated_direct_descent":counts["descent"],
        "eliminated_owner_barrier":counts["owner"],
        "surviving_cylinders":counts["survive"],
        "unbounded_lift_survivors":unbounded,
        "bounded_lift_survivors":bounded,
        "survivor_entropy_exponent":(
            math.log2(counts["survive"])/D if counts["survive"] else None),
        "survivors_without_monks_1_or_5_hit_in_prefix":no_monks_hit,
        "fixed_owner_events_examined_on_survivors":owner_event_total,
        "first_survivors":first,
    }

def main():
    depths=list(range(8,25))
    formal=[row(D,False) for D in depths]
    literature=[row(D,True) for D in depths]

    # Literature identity replay on a broad finite base set.  This checks the
    # map convention and criterion implementation; the theorem itself is
    # attributed to LaDue, not promoted from this finite replay.
    replay=0
    for m in range(3,1<<18,2):
        p=v2(m+1)
        q=((m+1)//(1<<p)-1)//2
        if (p&1)!=(q&1):
            continue
        a=m-1;b=m
        for _ in range(p+2):
            a=T(a);b=T(b)
        assert a==b
        replay+=1

    out={
      "schema":"COLLATZ_CRYSTAL_LITERATURE_SOURCE_AFFINE_V7",
      "map":"shortcut T(n)=n/2 if even else (3n+1)/2",
      "formal_only_rows":formal,
      "literature_augmented_rows":literature,
      "ladue_replay_instances_below_2pow18":replay,
      "warranted_inputs":[
        "minimal bad path has no direct descent",
        "Lean ownerLift source barrier on fixed high-valuation events",
        "V6 quarter splice is the k=1 owner barrier consequence"
      ],
      "external_literature_input":[
        "LaDue 2017 Theorem 4.1 consecutive-source synchronization criterion",
        "Monks et al. strongly sufficient set {1,5} mod 8 used diagnostically only"
      ],
      "interpretation_if_survivors_persist":(
        "finite-prefix residue/source-affine constructors do not close the "
        "ordinary-integer residual; the next representation must preserve "
        "cross-depth finite-support/source admission rather than choose a fresh "
        "2-adic lift at each depth"
      ),
      "universal_status":"UNKNOWN",
      "global_collatz":"UNKNOWN"
    }
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()
