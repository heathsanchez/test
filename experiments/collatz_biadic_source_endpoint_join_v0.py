#!/usr/bin/env python3
"""Exact Q2(endpoint) x Q3(source-lower-merge) compatibility audit.

Uses the qualified depth-20 V3 endpoint survivor language and the exact Q14
first-contracting predecessor quotient.  For each endpoint Q2 survivor prefix
we reconstruct its exact shortcut affine cocycle T^20(y)=(3^q y+B)/2^20.
This audit asks which source residues modulo 3^14 are forced by the affine
cocycle at the same 20-step word and whether those residues survive the exact
lower-merge sieve.  It is a compatibility experiment, not universal closure.
"""
import json
from pathlib import Path
import collatz_reverse_trit_bicell_v3_quotient as v3
import collatz_reverse_trit_bicell_v2 as v2
import collatz_reverse_predecessor_tree as rp

ADEPTH=20
Q=14
M3=3**Q

def qexp_of(A):
    q=0
    while A>1:
        assert A%3==0
        A//=3;q+=1
    return q

def run(out):
    parents,langs,rows=v3.evolve(ADEPTH)
    sets=[set(langs[ADEPTH][i]) for i in range(len(parents))]
    assert all(s==sets[0] for s in sets)
    E=sorted(sets[0])

    certs=rp.enumerate_first_contractions(Q)
    killed,selected=rp.quotient(certs,Q)

    live=[]; killed_count=0
    by_q={}
    for yres in E:
        A,B,_=v2.forward_affine(yres,ADEPTH)
        q=qexp_of(A)
        # For an exact 20-step endpoint word, the source/endpoint orientation
        # used here is n=yres as the word's starting integer.  Its residue mod
        # 3^14 is therefore exact and can be tested against the source sieve.
        # Record cocycle data so this orientation cannot be mistaken for the
        # Farey source->endpoint fiber in later promotion.
        s3=yres%M3
        dead=bool(killed[s3])
        by_q.setdefault(q,[0,0])
        by_q[q][dead]+=1
        if dead:killed_count+=1
        else:live.append(dict(endpoint_q2=yres,source_q3=s3,odd_count=q,B=B))

    result={
      "schema":"COLLATZ_BIADIC_SOURCE_ENDPOINT_JOIN_V0",
      "q2_depth":ADEPTH,"q3_depth":Q,
      "endpoint_survivors":len(E),
      "lower_merge_killed":killed_count,
      "joint_survivors":len(live),
      "odd_count_histogram":{str(k):{"live":v[0],"killed":v[1]} for k,v in sorted(by_q.items())},
      "first_joint_survivors":live[:200],
      "orientation_boundary":"This joins the 20-step endpoint-word starting integer to the Q14 source sieve. It is not yet the universal Farey source->endpoint affine fiber unless that identification is separately proved.",
      "verdict":"EMPTY_BOUNDED_JOIN" if not live else "EXACT_JOINT_RESIDUAL",
      "global_collatz":"UNKNOWN"
    }
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print("ENDPOINT_SURVIVORS",len(E))
    print("LOWER_MERGE_KILLED",killed_count)
    print("JOINT_SURVIVORS",len(live))
    print("VERDICT",result["verdict"])

if __name__=="__main__":
    run(Path("evidence/collatz-biadic-source-endpoint-join-v0/result.json"))
