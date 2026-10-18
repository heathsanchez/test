#!/usr/bin/env python3
"""Pre-outcome equivalence-class repair for the frozen AnyIO G2 policy gate.

This does not choose a repair or read the held-out future. It replaces policy-name
identity by exact scheduled-prefix identity before outcomes. The scientific point is
structural: 36 aliases become one noncold class, so a strict class-level winner is
mathematically possible where a strict named winner was not.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

from research.unified_consequence_runtime import (
    qualify_source_bound_g2_v9 as original,
    typed_v104_msi_bridge_v7 as bridge,
)

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
LOCK=U+"G2_TRAINING_NATIVE_CATALOG_LOCK_V1.json"
LOCK_COMMIT="fc5cbaf37fe55ab36b06de35e53bc08844791182"
POOL=U+"G2_SOURCE_DISTINCT_POOL_V1.json"
POOL_COMMIT="b90328c2315bd07d30bf7ddf05711e7431589aaf"


def git(repo: Path,*args: str,raw: bool=False):
    z=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return z if raw else z.decode().strip()


def frozen_json(path: str, commit: str):
    raw=git(ROOT,"show",commit+":"+path,raw=True)
    assert raw==(ROOT/path).read_bytes(),"FROZEN_INPUT_CHANGED:"+path
    return json.loads(raw)


def profile(prefix, positive):
    for i,candidate_id in enumerate(prefix):
        if candidate_id in positive:
            return (0,2*(i+1))
    return (1,2*len(prefix))


def dominates(a,b):
    return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))


def select_class(classes, positive):
    rows={key:profile(prefix,positive) for key,prefix in classes.items()}
    winners=[]
    for key,p in rows.items():
        if all(key==other or dominates(p,q) for other,q in rows.items()):
            winners.append(key)
    return winners,rows


def main(source: Path,v104: Path,msi: Path,out: Path):
    out.mkdir(parents=True,exist_ok=False)
    lock=frozen_json(LOCK,LOCK_COMMIT)
    pool=frozen_json(POOL,POOL_COMMIT)
    task=pool["case_pool"][0]
    assert git(source,"rev-parse","HEAD")==task["base"]
    assert git(v104,"rev-parse","HEAD")=="426c54f7c774560e0fabe7213c5ef333b1327c71"
    assert git(msi,"rev-parse","HEAD")=="56cfd7b523e3592cae4eafa5468f437ccb94dbe9"

    cat=bridge.catalog_v104_typed(
        source,task["base"],[r["path"] for r in task["production"]],
        v104,msi,cap=64,observation={},
    )
    raw=original.canonical(cat).encode()
    assert hashlib.sha256(raw).hexdigest()==lock["catalog_canonical_sha256"]
    horizon=lock["horizon_per_policy"]

    by_prefix=collections.defaultdict(list)
    for name,order in cat["orders"].items():
        by_prefix[tuple(order[:horizon])].append(name)
    assert sorted(map(len,by_prefix.values()))==[1,36],by_prefix

    cold_names=[names for prefix,names in by_prefix.items() if "COLD_V104_ORDER" in names]
    assert len(cold_names)==1 and cold_names[0]==["COLD_V104_ORDER"]
    cold_prefix=next(prefix for prefix,names in by_prefix.items() if "COLD_V104_ORDER" in names)
    noncold_prefix=next(prefix for prefix,names in by_prefix.items() if "COLD_V104_ORDER" not in names)
    noncold_names=sorted(next(names for prefix,names in by_prefix.items() if prefix==noncold_prefix))
    assert len(noncold_names)==36

    classes={"COLD":cold_prefix,"NONCOLD":noncold_prefix}
    ids=sorted(set(cold_prefix)|set(noncold_prefix))
    assert len(ids)==15

    census=collections.Counter()
    examples={}
    for mask in range(1<<len(ids)):
        positive={candidate_id for i,candidate_id in enumerate(ids) if mask>>i&1}
        winners,rows=select_class(classes,positive)
        label=(
            "UNIQUE_NONCOLD_CLASS" if winners==["NONCOLD"] else
            "UNIQUE_COLD_CLASS" if winners==["COLD"] else
            "CLASS_TIE"
        )
        census[label]+=1
        examples.setdefault(label,{
            "positive_candidate_ids":sorted(positive),
            "profiles":{k:list(v) for k,v in rows.items()},
            "winners":winners,
        })

    assert sum(census.values())==32768
    assert census["UNIQUE_NONCOLD_CLASS"]>0
    assert census["UNIQUE_COLD_CLASS"]>0
    assert census["CLASS_TIE"]>0

    # Alias invariance: renaming or dropping duplicate noncold names cannot alter
    # the class prefix or any class-level selection result.
    alias_digest=hashlib.sha256(
        json.dumps({"prefix":list(noncold_prefix),"members":noncold_names},
                   sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()

    result={
        "schema":"UDM_G2_EQUIVALENCE_CLASS_SELECTOR_V1",
        "status":"WARRANTED_BOUNDED_PREOUTCOME_POLICY_QUOTIENT",
        "catalog_sha256":hashlib.sha256(raw).hexdigest(),
        "horizon":horizon,
        "raw_policy_names":len(cat["orders"]),
        "policy_classes":2,
        "class_sizes":{"COLD":1,"NONCOLD":36},
        "scheduled_unique_candidates":len(ids),
        "noncold_alias_digest_sha256":alias_digest,
        "binary_outcome_census":dict(census),
        "class_examples":examples,
        "future_source":"UNOPENED",
        "native_candidate_runs":0,
        "G2":"UNKNOWN",
        "claim_boundary":"Structural repair of impossible named-unique gate only; no candidate success, no method acquisition, no held-out result.",
    }
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "raw_policy_names":result["raw_policy_names"],
        "policy_classes":result["policy_classes"],
        "class_sizes":result["class_sizes"],
        "binary_outcome_census":result["binary_outcome_census"],
        "G2":result["G2"],
    },sort_keys=True))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("v104",type=Path)
    p.add_argument("msi",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    main(a.source.resolve(),a.v104.resolve(),a.msi.resolve(),a.out.resolve())
