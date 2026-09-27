#!/usr/bin/env python3
"""Correctly oriented bounded source-product x lower-merge join.

For each exact 20-step parity cylinder n mod 2^20 surviving the V3 certificate
compiler, reconstruct q and B with
    2^20 * Y = 3^q * R + B.
At zero tail R is the actual source and Y is the endpoint residue.  We compute
the canonical R directly from the starting source cylinder and independently
check the affine identity, then apply the exact Q14 reverse-predecessor mask.
This is still a bounded cylinder audit, not a universal Collatz proof.
"""
import json
from pathlib import Path
import collatz_reverse_trit_bicell_v3_quotient as v3
import collatz_reverse_trit_bicell_v2 as v2
import collatz_reverse_predecessor_tree as rp

K=20; Q=14; M3=3**Q

def T(n): return (3*n+1)//2 if n&1 else n//2

def run(out):
    parents,langs,_=v3.evolve(K)
    sets=[set(langs[K][i]) for i in range(len(parents))]
    assert all(s==sets[0] for s in sets)
    source_cylinders=sorted(sets[0])
    killed,_=rp.quotient(rp.enumerate_first_contractions(Q),Q)
    rows=[]; dead=0
    for R in source_cylinders:
        A,B,Y=v2.forward_affine(R,K)
        q=0; z=A
        while z>1: assert z%3==0; z//=3; q+=1
        assert A==3**q
        assert (1<<K)*Y == A*R+B
        r3=R%M3
        isdead=bool(killed[r3])
        dead+=isdead
        if not isdead:
            rows.append({"source_q2":R,"source_q3":r3,"endpoint":Y,"odds":q,"bias":B})
    result={
      "schema":"COLLATZ_SOURCE_PRODUCT_ORIENTED_JOIN_V1",
      "q2_depth":K,"q3_depth":Q,
      "input_source_cylinders":len(source_cylinders),
      "lower_merge_killed":dead,
      "survivors":len(rows),
      "first_survivors":rows[:200],
      "affine_identity":"2^20*Y=3^q*R+B checked exactly for every cylinder",
      "orientation":"R is starting source residue; Y is its exact 20-step endpoint",
      "verdict":"EMPTY_BOUNDED_ORIENTED_JOIN" if not rows else "EXACT_BOUNDED_ORIENTED_RESIDUAL",
      "global_collatz":"UNKNOWN"
    }
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print("INPUT",len(source_cylinders),"KILLED",dead,"SURVIVORS",len(rows))
    print("VERDICT",result["verdict"])

if __name__=="__main__":
    run(Path("evidence/collatz-source-product-oriented-join-v1/result.json"))
