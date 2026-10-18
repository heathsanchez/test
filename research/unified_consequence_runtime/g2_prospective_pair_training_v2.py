#!/usr/bin/env python3
"""Prospective training gate for the frozen G2 V2 pair.

No target-specific source coordinates or repair templates live here. The method
functions are imported from the previously qualified AnyIO V2 authority after
byte-identity checks against that exact qualified commit.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PREQUERY=Path("research/unified_consequence_runtime/G2_PROSPECTIVE_PAIR_PREQUERY_V2.json")
ROLES=Path("research/unified_consequence_runtime/G2_PROSPECTIVE_PAIR_ROLE_MANIFEST_V2.json")
PREQUERY_COMMIT="bfa8b0ffa0874231d3fe0b3bfa5d21fdb950488f"
ROLE_COMMIT="a96afabe52abb60a899e17465a3c152fd2c7da92"
METHOD_COMMIT="094e2ddc3ba601a00eaf368151172a361e5542da"
METHOD_FILES=[
 "research/unified_consequence_runtime/G2_MUTABLE_CLOSURE_EQUIVALENCE_FIX_PROTOCOL_V2.json",
 "research/unified_consequence_runtime/g2_mutable_closure_trace_plugin_v2.py",
 "research/unified_consequence_runtime/g2_anyio_mutable_closure_equivalence_fix_v2.py",
 "research/unified_consequence_runtime/qualify_g2_anyio_mutable_closure_equivalence_fix_v2.py",
]


def git(repo:Path,*args:str,raw=False):
    out=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return out if raw else out.decode().strip()


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def frozen_json(path:Path,commit:str):
    live=(ROOT/path).read_bytes()
    frozen=git(ROOT,"show",f"{commit}:{path}",raw=True)
    if live!=frozen:
        raise ValueError(f"FROZEN_FILE_CHANGED:{path}")
    return json.loads(frozen)


def verify_method():
    receipts={}
    for name in METHOD_FILES:
        live=(ROOT/name).read_bytes()
        frozen=git(ROOT,"show",f"{METHOD_COMMIT}:{name}",raw=True)
        if live!=frozen:
            raise ValueError(f"QUALIFIED_METHOD_CHANGED:{name}")
        receipts[name]=sha(live)
    return receipts


def callable_map(raw:bytes):
    tree=ast.parse(raw.decode("utf-8"))
    out={}
    def walk_class(node,prefix):
        for child in node.body:
            if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)) and child.name.startswith("test"):
                key="::".join([*prefix,child.name])
                out[key]=ast.dump(child,include_attributes=False)
            elif isinstance(child,ast.ClassDef) and child.name.startswith("Test"):
                walk_class(child,[*prefix,child.name])
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test"):
            out[node.name]=ast.dump(node,include_attributes=False)
        elif isinstance(node,ast.ClassDef) and node.name.startswith("Test"):
            walk_class(node,[node.name])
    return out


def changed_nodes(base_raw:bytes,head_raw:bytes):
    base=callable_map(base_raw)
    head=callable_map(head_raw)
    return sorted(name for name,value in head.items() if base.get(name)!=value)


def main(world:Path,triskelion:Path,msi:Path,base_test:Path,head_test:Path,out:Path):
    pre=frozen_json(PREQUERY,PREQUERY_COMMIT)
    roles=frozen_json(ROLES,ROLE_COMMIT)
    method_hashes=verify_method()
    role=next(x for x in roles["selected"] if x["role"]=="TRAINING")
    if role["repository"]!="python-attrs/attrs" or role["pr"]!=1593:
        raise ValueError("TRAINING_ROLE_CHANGED")
    if git(world,"rev-parse","HEAD")!=role["base"]:
        raise ValueError("TRAINING_BASE_CHANGED")
    production=role["production"][0]
    test_path=role["author_tests"][0]
    original=(world/production).read_bytes()
    author=(world/test_path).read_bytes()
    if author!=head_test.read_bytes():
        raise ValueError("AUTHOR_TEST_OVERLAY_MISMATCH")
    if base_test.read_bytes()==head_test.read_bytes():
        raise ValueError("AUTHOR_TEST_HAS_NO_CHANGE")
    if git(world,"diff","--name-only").splitlines()!=[test_path]:
        raise ValueError("UNEXPECTED_WORKTREE_OVERLAY")

    nodes=changed_nodes(base_test.read_bytes(),head_test.read_bytes())
    result={
      "schema":"UDM_G2_PROSPECTIVE_PAIR_TRAINING_V2",
      "status":"UNKNOWN",
      "training_repository":role["repository"],
      "training_pr":role["pr"],
      "training_base":role["base"],
      "training_head_test":role["head"],
      "production_path":production,
      "author_test_path":test_path,
      "production_sha256":sha(original),
      "author_test_sha256":sha(author),
      "derived_changed_test_nodes":nodes,
      "method_authority_commit":METHOD_COMMIT,
      "method_file_sha256":method_hashes,
      "future_repository":"tox-dev/tox",
      "future_source":"SEALED_UNOPENED",
      "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
    }
    out.mkdir(parents=True,exist_ok=False)
    (out/"DERIVED_TEST_NODES.json").write_text(json.dumps(nodes,indent=2)+"\n")
    if not nodes:
        result["status"]="UNKNOWN_NO_MECHANICALLY_DERIVED_AUTHOR_TEST_NODE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    # Import only after exact method verification.
    from research.unified_consequence_runtime import g2_anyio_mutable_closure_equivalence_fix_v2 as method

    node_args=[str(world/test_path)+"::"+node for node in nodes]
    baseline=method.run_pytest(world,node_args,out/"baseline-native",timeout=180)
    result["baseline"]=baseline
    if (
        baseline["returncode"] not in (1,)
        or baseline["counts"]["tests"]<=0
        or baseline["counts"]["failures"]<=0
        or baseline["counts"]["errors"]!=0
    ):
        result["status"]="UNKNOWN_NO_AUTHENTIC_TRAINING_PROTECTED_FAILURE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    patterns=method.scan_patterns(production,original)
    result["patterns"]=patterns
    result["pattern_count"]=len(patterns)
    quotient=method.policy_classes(world,triskelion,msi,production)
    result["policy_quotient"]=quotient
    if not patterns:
        result["status"]="UNKNOWN_NO_QUALIFIED_MUTABLE_CLOSURE_PATTERN"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    observed=method.run_pytest(world,node_args,out/"observer-native",patterns=patterns,timeout=180)
    result["observer_native"]=observed
    checks=[method.trace_has_stale_capture(p,observed["trace_events"]) for p in patterns]
    result["observer_checks"]=checks
    passing=[i for i,x in enumerate(checks) if x["pass"]]
    if (
        observed["counts"]["tests"]<=0
        or observed["counts"]["failures"]<=0
        or observed["counts"]["errors"]!=0
        or not passing
    ):
        result["status"]="UNKNOWN_NO_NATIVE_STALE_CLOSURE_CAPTURE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    candidates=[]
    for idx in passing:
        p=patterns[idx]
        repaired=method.repair_source(original,p)
        candidates.append({
          "pattern":p,
          "source":repaired,
          "source_sha256":sha(repaired),
          "candidate_id":"mutable-closure-repair:"+sha(repaired)[:24],
        })
    result["candidate_schedule"]=[
      {"candidate_id":c["candidate_id"],"pattern_id":c["pattern"]["pattern_id"],"source_sha256":c["source_sha256"]}
      for c in candidates
    ]

    winner=None
    evaluations=[]
    for i,candidate in enumerate(candidates):
        (world/production).write_bytes(candidate["source"])
        first=method.run_pytest(world,node_args,out/f"repair-{i:02d}-a",timeout=180)
        second=method.run_pytest(world,node_args,out/f"repair-{i:02d}-b",timeout=180)
        full=method.run_pytest(world,[str(world/test_path)],out/f"repair-{i:02d}-full",timeout=300)
        good=(
          first["returncode"]==0 and first["counts"]["tests"]>0 and first["counts"]["failures"]==0 and first["counts"]["errors"]==0
          and second["returncode"]==0 and second["counts"]["tests"]>0 and second["counts"]["failures"]==0 and second["counts"]["errors"]==0
          and full["returncode"]==0 and full["counts"]["tests"]>0 and full["counts"]["failures"]==0 and full["counts"]["errors"]==0
        )
        evaluations.append({
          "candidate_id":candidate["candidate_id"],"pattern_id":candidate["pattern"]["pattern_id"],
          "source_sha256":candidate["source_sha256"],"protected_first":first,"protected_second":second,
          "full_author_file":full,"pass":good
        })
        if good and winner is None:
            winner=candidate
    result["candidate_evaluations"]=evaluations
    if winner is None:
        (world/production).write_bytes(original)
        result["status"]="REJECTED_NO_NATIVE_TRAINING_REPAIR"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    (world/production).write_bytes(original)
    withdrawal=method.run_pytest(world,node_args,out/"withdrawal-native",timeout=180)
    result["withdrawal"]=withdrawal
    if not (
      withdrawal["returncode"]==1 and withdrawal["counts"]["tests"]>0
      and withdrawal["counts"]["failures"]>0 and withdrawal["counts"]["errors"]==0
    ):
        result["status"]="UNKNOWN_WITHDRAWAL_DID_NOT_RESTORE_FAILURE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    (world/production).write_bytes(winner["source"])
    restoration=method.run_pytest(world,node_args,out/"restoration-native",timeout=180)
    result["restoration"]=restoration
    if not (
      restoration["returncode"]==0 and restoration["counts"]["tests"]>0
      and restoration["counts"]["failures"]==0 and restoration["counts"]["errors"]==0
    ):
        result["status"]="UNKNOWN_RESTORATION_NOT_REVERIFIED"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    result["training_repair"]={
      "candidate_id":winner["candidate_id"],"pattern_id":winner["pattern"]["pattern_id"],
      "source_sha256":winner["source_sha256"],"causal_withdrawal":True,"restoration":True
    }
    result["status"]="WARRANTED_BOUNDED_PROSPECTIVE_TRAINING_ACQUISITION_FUTURE_STILL_SEALED"
    (out/"GENERATED_REPAIR.py").write_bytes(winner["source"])
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


if __name__=="__main__":
    if len(sys.argv)!=7:
        raise SystemExit("usage: g2_prospective_pair_training_v2.py WORLD V104 MSI BASE_TEST HEAD_TEST OUT")
    r=main(*(Path(x).resolve() for x in sys.argv[1:]))
    print(json.dumps({
      "status":r.get("status"),"changed_nodes":r.get("derived_changed_test_nodes"),
      "pattern_count":r.get("pattern_count"),"future_source":r.get("future_source"),"G2":r.get("G2")
    },sort_keys=True))
    raise SystemExit(0 if r.get("status") in {
      "WARRANTED_BOUNDED_PROSPECTIVE_TRAINING_ACQUISITION_FUTURE_STILL_SEALED",
      "UNKNOWN_NO_QUALIFIED_MUTABLE_CLOSURE_PATTERN",
      "UNKNOWN_NO_NATIVE_STALE_CLOSURE_CAPTURE",
      "REJECTED_NO_NATIVE_TRAINING_REPAIR",
    } else 2)
