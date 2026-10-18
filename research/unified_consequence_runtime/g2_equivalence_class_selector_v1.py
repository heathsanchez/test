#!/usr/bin/env python3
"""Pre-outcome equivalence-class repair for the frozen AnyIO G2 policy gate.

Consumes the exact pre-native source-only catalog artifact. It never regenerates the
catalog, reads candidate outcomes, or touches the held-out future. Policy identity is
quotiented by exact scheduled prefix before Pareto comparison.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import zipfile

CATALOG_ZIP_SHA256="3140ce752b3b9b43cba6aafbe914c6e5f48a22f350237965e7ca5ab4edb411ae"
CATALOG_CANONICAL_SHA256="7199e478dc9c5dd247571559475bcdbfaa8e737ac21c39bf179cbbe977f4d9c6"
HORIZON=8


def sha256(raw: bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def profile(prefix, positive):
    for i,candidate_id in enumerate(prefix):
        if candidate_id in positive:
            return (0,2*(i+1))
    return (1,2*len(prefix))


def dominates(a,b):
    return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))


def quotient_policies(orders):
    groups=collections.defaultdict(list)
    for name,order in orders.items():
        groups[tuple(order[:HORIZON])].append(name)
    return groups


def select_class(classes, positive):
    rows={key:profile(prefix,positive) for key,prefix in classes.items()}
    winners=[
        key for key,p in rows.items()
        if all(key==other or dominates(p,q) for other,q in rows.items())
    ]
    return winners,rows


def main(archive: Path,out: Path):
    out.mkdir(parents=True,exist_ok=False)
    raw_zip=archive.read_bytes()
    assert sha256(raw_zip)==CATALOG_ZIP_SHA256,"CATALOG_ARTIFACT_DIGEST_MISMATCH"
    with zipfile.ZipFile(archive) as z:
        raw=z.read("catalog/COMPLETE_ORIGINAL_CATALOG.json").strip()
        index=json.loads(z.read("catalog/SOURCE_ONLY_INDEX.json"))
    assert sha256(raw)==CATALOG_CANONICAL_SHA256==index["complete_catalog_sha256"]
    catalog=json.loads(raw)
    assert len(catalog["rows"])==64 and len(catalog["orders"])==37

    groups=quotient_policies(catalog["orders"])
    sizes=sorted(map(len,groups.values()))
    assert sizes==[1,36],sizes
    cold_prefix=next(prefix for prefix,names in groups.items() if "COLD_V104_ORDER" in names)
    cold_names=groups[cold_prefix]
    assert cold_names==["COLD_V104_ORDER"]
    noncold_prefix=next(prefix for prefix,names in groups.items() if "COLD_V104_ORDER" not in names)
    noncold_names=sorted(groups[noncold_prefix])
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

    expected={
        "UNIQUE_NONCOLD_CLASS":10933,
        "UNIQUE_COLD_CLASS":10917,
        "CLASS_TIE":10918,
    }
    assert dict(census)==expected,(dict(census),expected)

    result={
        "schema":"UDM_G2_EQUIVALENCE_CLASS_SELECTOR_V1",
        "status":"WARRANTED_BOUNDED_PREOUTCOME_POLICY_QUOTIENT",
        "source_catalog_artifact_id":12117742923,
        "source_catalog_zip_sha256":CATALOG_ZIP_SHA256,
        "catalog_canonical_sha256":CATALOG_CANONICAL_SHA256,
        "horizon":HORIZON,
        "raw_policy_names":37,
        "policy_classes":2,
        "class_sizes":{"COLD":1,"NONCOLD":36},
        "scheduled_unique_candidates":15,
        "binary_outcome_census":dict(census),
        "class_examples":examples,
        "selection_rule":"Compare exact prefix-equivalence classes, never policy aliases; authorize only unique noncold class.",
        "future_source":"UNOPENED",
        "native_candidate_runs":0,
        "G2":"UNKNOWN",
        "claim_boundary":"Structural repair of impossible named-unique gate only; no candidate success, no method acquisition, no held-out result.",
    }
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "raw_policy_names":37,
        "policy_classes":2,
        "class_sizes":result["class_sizes"],
        "binary_outcome_census":result["binary_outcome_census"],
        "G2":"UNKNOWN",
    },sort_keys=True))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("catalog_zip",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    main(a.catalog_zip.resolve(),a.out.resolve())
