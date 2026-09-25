#!/usr/bin/env python3
"""
Choose the minimum sufficient finite-group context subset for ACC Future Quotient.

Evidence boundary:
- V3 produced 56 false future-quotient portals.
- Six-context synchronized finite-group projection separates 56/56 but almost
  collapses the Atlas to exact identity (433270 classes / 433272 states).

This selector enumerates all 63 non-empty context subsets, keeps only subsets
that separate every V3 false portal, minimizes context count, then minimizes the
number of (V1 future signature × selected projection) Atlas classes.  It does
not search for proofs and has no certificate authority.
"""

import argparse, hashlib, json, sqlite3, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from acc_competitive import finite_group_pdb_v1 as fg
from acc_competitive.atlas_fiber_refinement_v1 import contexts, project
from acc_competitive.future_quotient_v2 import decode_state, digest_parts
from acc_competitive.future_quotient_v4 import refined_signature2_for_audit

def ctx_digest(pair):
    return digest_parts((pair,))

def selected_digest(digests,mask):
    return digest_parts(tuple(d for i,d in enumerate(digests) if mask & (1<<i)))

def false_contacts(v2_index,v3_dir,total_cap):
    ctxs=contexts(fg)
    db=sqlite3.connect(v2_index)
    contacts=[]
    for p in sorted(Path(v3_dir).rglob("results.json")):
        obj=json.loads(p.read_text())
        cases=obj if isinstance(obj,list) else [obj]
        for case in cases:
            for ex in case.get("separator_examples",[]):
                q=decode_state(bytes.fromhex(ex["query_state"]))
                fs=bytes.fromhex(ex["future_sig"])
                q2=refined_signature2_for_audit(q,total_cap)
                qproj=project(fg,q,ctxs)
                reps=[]
                for rk,d,nm,rank in db.execute(
                    "SELECT state,distance,next_move,rep_rank FROM future_representatives WHERE signature=? ORDER BY rep_rank",
                    (fs,)):
                    r=decode_state(rk)
                    if refined_signature2_for_audit(r,total_cap)!=q2:
                        continue
                    rproj=project(fg,r,ctxs)
                    diff=0
                    for i,(a,b) in enumerate(zip(qproj,rproj)):
                        if a!=b: diff|=1<<i
                    reps.append({"diff_mask":diff,"distance":int(d),"rank":int(rank)})
                if not reps:
                    raise RuntimeError(f"cannot reproduce V3 contact {case.get('challenge_id')} {fs.hex()}")
                contacts.append({
                    "challenge_id":case.get("challenge_id"),
                    "query_depth":ex.get("query_depth"),
                    "future_sig":fs.hex(),
                    "failure_reason":(ex.get("rollout_failure") or {}).get("reason"),
                    "rep_diff_masks":[r["diff_mask"] for r in reps],
                })
    db.close()
    return ctxs,contacts

def separates(mask,contact):
    return all(mask & d for d in contact["rep_diff_masks"])

def popcount(x): return x.bit_count()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--v2-index",required=True)
    ap.add_argument("--v3-dir",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--total-cap",type=int,default=10000)
    a=ap.parse_args()

    ctxs,contacts=false_contacts(a.v2_index,a.v3_dir,a.total_cap)
    if len(contacts)!=56:
        raise RuntimeError(f"expected exact V3 false-contact boundary 56, got {len(contacts)}")

    census=[]
    full=[]
    for mask in range(1,1<<len(ctxs)):
        n=sum(separates(mask,c) for c in contacts)
        rec={"mask":mask,"bits":popcount(mask),"separated":n,
             "contexts":[ctxs[i][0] for i in range(len(ctxs)) if mask&(1<<i)]}
        census.append(rec)
        if n==len(contacts): full.append(rec)
    if not full: raise RuntimeError("no context subset separates all V3 false contacts")

    min_bits=min(r["bits"] for r in full)
    minimal=[r for r in full if r["bits"]==min_bits]
    candidate_masks={r["mask"] for r in minimal}

    # One pass over the Atlas observations. Compute all six projections once,
    # then track exact combined class identities for only the minimum-cardinality
    # candidate masks.
    db=sqlite3.connect(a.v2_index)
    class_sets={m:set() for m in candidate_masks}
    rows=0
    for state,fs in db.execute("SELECT state,future_sig FROM observations"):
        s=decode_state(state)
        ds=[ctx_digest(x) for x in project(fg,s,ctxs)]
        for m in candidate_masks:
            key=hashlib.sha256(bytes(fs)+selected_digest(ds,m)).digest()
            class_sets[m].add(key)
        rows+=1
        if rows%50000==0:
            print("FQ5_SELECTOR_PROGRESS",json.dumps({"states":rows},sort_keys=True),flush=True)
    db.close()

    for r in minimal:
        r["atlas_product_classes"]=len(class_sets[r["mask"]])
        r["atlas_compression"]=rows-len(class_sets[r["mask"]])
        r["class_fraction"]=len(class_sets[r["mask"]])/rows

    minimal.sort(key=lambda r:(r["atlas_product_classes"],r["mask"]))
    selected=minimal[0]
    result={
        "version":"acc-future-quotient-v5-context-selector",
        "status":"CANDIDATE_MINIMUM_SUFFICIENT_GUARD",
        "atlas_states":rows,
        "v3_false_contacts":len(contacts),
        "all_contexts":[x[0] for x in ctxs],
        "subset_census":census,
        "minimum_context_count":min_bits,
        "minimum_full_separator_subsets":minimal,
        "selected":selected,
        "claim_boundary":"Selection is diagnostic/search-only: minimum context count that separates all 56 frozen V3 false portals, tie-broken by fewest V1-future × projection Atlas classes. No proof or state equality follows."
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ACC_FUTURE_QUOTIENT_V5_SELECTOR",json.dumps({
        "atlas_states":rows,"v3_false_contacts":len(contacts),
        "minimum_context_count":min_bits,
        "candidate_subsets":len(minimal),
        "selected":selected
    },sort_keys=True))

if __name__=="__main__":main()
