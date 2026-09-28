#!/usr/bin/env python3
"""Crystal V8: exact post-diagonal source↔endpoint fiber reduction.

No new residue bank is built.  We retain the V7 actual-source semantics and
split at q=n, where q is the number of accelerated odd steps already taken.

For an exact accelerated prefix
    2^D y = 3^q n + B,
source recovery is exact.  If q>=n>=3 and a later endpoint returns to the
source-relative band y<=4n, then
    y <= 4n <= 4q < 3^q.
Hence the source-coherence congruence
    2^D y == B (mod 3^q)
has its canonical endpoint representative equal to the ordinary integer y
itself.  The universal residual is therefore either:
  (A) permanent post-diagonal escape above 4n, or
  (B) a source-admitted linearly-small canonical endpoint residue y<=4q.

The finite corpus below is only a falsifier/diagnostic for this exact reduction.
It is not used to promote the universal disjunction to closure.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

def v2(z:int)->int:
    assert z>0
    return (z & -z).bit_length()-1

def odd_step(y:int):
    z=3*y+1
    a=v2(z)
    return z>>a,a

def endpoint_residue(B:int,D:int,q:int)->int:
    m=3**q
    return (B*pow(pow(2,D,m),-1,m))%m

def run(limit:int, odd_cap:int, out:Path):
    counts=Counter()
    diagonal=[]
    postdiag_returns=[]
    first_unresolved=[]
    for n in range(3,limit,2):
        counts["tested_odd_sources"]+=1
        y=n; q=0; D=0; B=0
        reached_diag=False
        first_diag=None
        while q<=odd_cap:
            # Exact source fiber at every odd endpoint.
            assert (1<<D)*y == (3**q)*n+B
            if y<n:
                counts["exit_descent"]+=1
                break
            if y<=4*n and y%8==5:
                counts["exit_quarter_splice"]+=1
                if reached_diag:
                    counts["postdiag_return_splice"]+=1
                    r=endpoint_residue(B,D,q)
                    assert n<=q and n>=3 and y<=4*n and y<=4*q and 4*q<3**q
                    assert r==y
                    postdiag_returns.append({
                        "n":n,"q":q,"D":D,"B":B,"y":y,
                        "canonical_endpoint_residue":r,
                        "source_recovered":(((1<<D)*y-B)//(3**q)),
                        "kind":"quarter_splice"})
                break

            if q>=n and not reached_diag:
                reached_diag=True
                first_diag=(q,D,B,y)
                counts["diagonal_entrants"]+=1
                # Any non-exit entry in the source band would be the exact
                # post-diagonal obstruction.  The frozen corpus currently has none.
                if y<=4*n:
                    counts["diagonal_entry_band_nonexit"]+=1
                else:
                    counts["diagonal_entry_above_band"]+=1

            if reached_diag and y<=4*n:
                # A non-splice/non-descent post-diagonal band return.
                counts["postdiag_return_nonexit"]+=1
                r=endpoint_residue(B,D,q)
                assert n<=q and n>=3 and y<=4*n and y<=4*q and 4*q<3**q
                assert r==y
                postdiag_returns.append({
                    "n":n,"q":q,"D":D,"B":B,"y":y,
                    "canonical_endpoint_residue":r,
                    "source_recovered":(((1<<D)*y-B)//(3**q)),
                    "kind":"nonexit"})
                # Continue: this is a falsifier, not assumed impossible.

            y2,a=odd_step(y)
            # Exact cocycle update:
            # 2^(D+a)y' = 3^(q+1)n + (3B+2^D)
            B=3*B+(1<<D)
            D+=a
            q+=1
            y=y2
        else:
            pass
        if q>odd_cap:
            counts["odd_cap_unresolved"]+=1
            if len(first_unresolved)<20:
                first_unresolved.append([n,q,y])
        if first_diag is not None and len(diagonal)<40:
            q0,D0,B0,y0=first_diag
            diagonal.append({"n":n,"q":q0,"D":D0,"B":B0,"y":y0,
                             "ratio_num":y0,"ratio_den":n})

    result={
        "schema":"COLLATZ_CRYSTAL_SOURCE_FIBER_V8",
        "limit":limit,
        "odd_cap":odd_cap,
        "counts":dict(sorted(counts.items())),
        "first_diagonal_entrants":diagonal,
        "postdiagonal_band_returns":postdiag_returns[:100],
        "first_unresolved":first_unresolved,
        "universal_reduction":{
            "prediagonal_resource":"n-q strictly decreases by one per accelerated odd step while q<n",
            "postdiagonal_band_fiber":"q>=n>=3 and y<=4n imply y<=4q<3^q; exact affine source coherence makes y the canonical endpoint residue modulo 3^q",
            "remaining_disjunction":[
                "eventually stay above 4n forever without OrdinaryExit",
                "realize a source-admitted canonical endpoint residue y<=4q"
            ]
        },
        "claim_boundary":"The arithmetic source-fiber reduction is exact. Corpus counts are bounded falsification evidence only and do not rule out permanent high escape or universal small-residue realization.",
        "universal_status":"UNKNOWN",
        "global_collatz":"UNKNOWN"
    }
    if counts.get("postdiag_return_nonexit",0):
        result["verdict"]="EXACT_POSTDIAGONAL_BAND_NONEXIT_FALSIFIER"
    elif counts.get("odd_cap_unresolved",0):
        result["verdict"]="BOUNDED_DIAGNOSTIC_CENSORED"
    else:
        result["verdict"]="PASS_BOUNDED_POSTDIAGONAL_RETURNS_EXIT"
    body=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["closure_certificate"]=hashlib.sha256(body.encode()).hexdigest()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=1<<20)
    ap.add_argument("--odd-cap",type=int,default=4096)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.limit,a.odd_cap,a.output)
