#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

LETTER={1:"x",-1:"X",2:"y",-2:"Y"}
CONJ={
    (1,"x"):7,(1,"X"):6,(1,"y"):9,(1,"Y"):8,
    (2,"x"):11,(2,"X"):10,(2,"y"):13,(2,"Y"):12,
}
SWAP=(0,1,2,0,4,3)


def to_pair(initial):
    return tuple("".join(LETTER[int(a)] for a in w) for w in initial)


def compile_elementary(moves):
    out=[]
    for m in moves:
        op=m.get("op")
        if op=="invert":
            t=int(m["target"]); out.append(0 if t==1 else 1)
        elif op=="multiply":
            t,s=int(m["target"]),int(m["source"])
            if (t,s)==(1,2): out.append(2)
            elif (t,s)==(2,1): out.append(4)
            else: raise ValueError(("bad multiply",m))
        elif op=="conjugate":
            out.append(CONJ[(int(m["target"]),str(m["by"]))])
        elif op=="swap":
            out.extend(SWAP)
        else:
            raise ValueError(("unknown elementary op",m))
    return out


def classify(*, solved, official_ok, live_best, official_length, elem_counts, elementary_ops):
    if not solved:
        return "public-route-unsolved"
    if not official_ok:
        return "official-transport-invalid"
    excess=max(1,int(official_length)-int(live_best))
    swap_expansion=int(official_length)-int(elementary_ops)
    if swap_expansion*2>excess:
        return "swap-expansion-dominant"

    core={
        "conjugation-dominant":int(elem_counts.get("conjugate",0)),
        "multiply-dominant":int(elem_counts.get("multiply",0)),
        "invert-dominant":int(elem_counts.get("invert",0)),
    }
    peak=max(core.values()) if core else 0
    leaders=[k for k,v in core.items() if v==peak and peak>0]
    if len(leaders)==1:
        return leaders[0]
    return "mixed-elementary-cost"


NEXT_ACTION={
    "public-route-unsolved":"cost-native search still requires a connectivity proposal for this atom",
    "official-transport-invalid":"repair transport/decoder semantics before cost optimization",
    "swap-expansion-dominant":"eliminate or amortize basis-return/swap transport in the official-cost-native proposal language",
    "conjugation-dominant":"make conjugator transport a first-class charged proposal coordinate",
    "multiply-dominant":"bias cost-native proposals toward direct official multiply structure",
    "invert-dominant":"collapse avoidable inversion churn in the official-cost proposal graph",
    "mixed-elementary-cost":"retain the exact mixed cost vector and require a multi-coordinate cost-native proposal",
}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--pool-results",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--budget",type=int,default=1000)
    ap.add_argument("--count",type=int,default=64)
    a=ap.parse_args()

    acc=Path(a.acc_root); axs=Path(a.acsolverx_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    sys.path.insert(0,str(axs))
    from research.ac_hashfree_cascade_20260914 import hfcascade, verify as public_verify
    from research.supermoves_20260908 import certificate_decoder

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}
    pool=json.loads(Path(a.pool_results).read_text())
    pool_by_id={r["challenge_id"]:r for r in pool}
    ordered=sorted(
        pool_by_id,
        key=lambda cid:(hashlib.sha256(cid.encode()).hexdigest(),cid)
    )
    selected=ordered[:a.count]
    assert len(selected)==a.count,(len(selected),a.count)

    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    rows=[]; child_counts=Counter()
    t0=time.time()

    for cid in selected:
        prior=pool_by_id[cid]
        challenge=byid[cid]
        live_best=int(prior["live_best"])
        pair=to_pair(challenge["initial_relators"])
        rec={
            "challenge_id":cid,
            "selection_hash":hashlib.sha256(cid.encode()).hexdigest(),
            "live_best":live_best,
            "prior_solved":bool(prior.get("solved")),
            "prior_official_ok":bool(prior.get("official_ok")),
        }
        try:
            res=hfcascade.solve(
                pair,budget=a.budget,score="s20",gates=True,pair_descent=True,
                engine="fast",closed_set="sorted",nielsen=True,perms=True,
                gate_when="pop",
            )
            solved=bool(res["solved"])
            if solved != bool(prior.get("solved")):
                raise AssertionError(("frozen solver replay changed solved status", cid, solved, prior.get("solved")))
            rec.update({
                "solved":solved,
                "mixed_steps":res.get("path_length"),
                "units":res.get("units"),
                "stage":res.get("stage"),
            })
            if not solved:
                child="public-route-unsolved"
                rec.update({
                    "official_ok":False,
                    "elementary_ops":None,
                    "official_length":None,
                    "elementary_op_counts":{},
                    "swap_expansion":None,
                })
            else:
                public_verify.replay(pair,res["steps"],res["states"])
                elem=certificate_decoder.decode_elementary(pair,res["states"],res["steps"])
                counts=Counter(str(m.get("op")) for m in elem)
                official=compile_elementary(elem)
                verdict=core.verify(
                    challenge,official,challenge["move_spec_version"],limits
                )
                official_ok=bool(verdict.get("ok"))
                if official_ok != bool(prior.get("official_ok")):
                    raise AssertionError(("frozen official replay changed verifier status", cid, official_ok, prior.get("official_ok")))
                child=classify(
                    solved=True,
                    official_ok=official_ok,
                    live_best=live_best,
                    official_length=len(official),
                    elem_counts=counts,
                    elementary_ops=len(elem),
                )
                rec.update({
                    "official_ok":official_ok,
                    "elementary_ops":len(elem),
                    "official_length":len(official),
                    "elementary_op_counts":dict(counts),
                    "swap_expansion":len(official)-len(elem),
                    "official_excess":len(official)-live_best,
                    "official_certificate_hash":verdict.get("certificate_hash"),
                })
        except Exception as exc:
            # A replay/decoder exception is an exact transport failure, not
            # evidence for a cost family.
            child="official-transport-invalid"
            rec.update({
                "error":f"{type(exc).__name__}: {exc}",
                "official_ok":False,
            })

        rec.update({
            "parent_residual":"acc.official_cost_native_search",
            "child_residual":child,
            "credited":True,
            "next_action":NEXT_ACTION[child],
        })
        child_counts[child]+=1
        rows.append(rec)
        print("ACC_COST_ATOM",json.dumps(rec,sort_keys=True),flush=True)

    elapsed=time.time()-t0
    credited=sum(bool(r["credited"]) for r in rows)
    result={
        "schema":"acc.official-cost-driver-quotient.v1",
        "calibration_contract":"metalogiclabs/mathgraph@2d59a95ab6c28c1a1814863ab9becaaba9c83356",
        "calibration_manifest":"metalogiclabs/mathgraph@677c4ed337eee4f863d160600bd81de782f16803",
        "authority_sha":"aa59722ab62c83a427a9bc9e8a41293d82d1b6af",
        "public_solver_commit":"5ae1bd8eda6d80dfbea51680636f825da19fb802",
        "official_commit":"99a65377c5c4f412cd9af7b8d31c41464a855736",
        "parent_residual":"acc.official_cost_native_search",
        "selection_rule":"first 64 challenge ids by sha256(challenge_id) over frozen 2213-row pool",
        "frozen_atoms":len(rows),
        "credited_atoms":credited,
        "contraction_fraction":credited/len(rows),
        "child_counts":dict(child_counts),
        "rows":rows,
        "scientific_elapsed_seconds":elapsed,
        "search_retuned":False,
        "submission_attempted":False,
        "status":"WARRANTED_BOUNDED_COST_DRIVER_QUOTIENT",
        "boundary":"Cost-driver residual refinement only. No leaderboard win or solver improvement is claimed.",
    }
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ACC_COST_SUMMARY",json.dumps({
        "frozen_atoms":result["frozen_atoms"],
        "credited_atoms":result["credited_atoms"],
        "contraction_fraction":result["contraction_fraction"],
        "child_counts":result["child_counts"],
        "scientific_elapsed_seconds":result["scientific_elapsed_seconds"],
    },sort_keys=True))


if __name__=="__main__":
    main()
