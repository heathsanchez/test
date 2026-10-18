#!/usr/bin/env python3
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main(result_root: Path, anyio_root: Path, out: Path) -> None:
    r=json.loads((result_root/"RESULT.json").read_text())
    assert r["status"]=="WARRANTED_BOUNDED_POSTHOC_TRAINING_REPAIR_AND_CLASS_SELECTOR", r.get("status")
    assert r["G2"]=="UNKNOWN" and r["heldout_future"]=="UNOPENED"
    assert r["author_repaired_production_read"] is False
    assert r["pattern_count"]>=1
    assert any(x["pass"] for x in r["observer_checks"])
    q=r["policy_quotient"]
    assert q["policy_name_count"]==37 and q["class_count"]==2
    cold=[x for x in q["classes"] if x["is_cold"]]
    warm=[x for x in q["classes"] if not x["is_cold"]]
    assert len(cold)==len(warm)==1
    assert len(cold[0]["members"])==1 and len(warm[0]["members"])==36
    assert r["selection"]["unit"]=="EQUIVALENCE_CLASS_NOT_POLICY_NAME"
    assert r["selection"]["old_noncold_alias_count"]==36
    assert r["training_repair"]["causal_withdrawal"] is True
    assert r["training_repair"]["restoration"] is True
    assert r["withdrawal"]["counts"]=={"tests":2,"failures":2,"errors":0,"skipped":0}
    assert r["restoration"]["counts"]=={"tests":2,"failures":0,"errors":0,"skipped":0}

    generated=(result_root/"GENERATED_REPAIR.py").read_bytes()
    assert hashlib.sha256(generated).hexdigest()==r["training_repair"]["source_sha256"]
    base=subprocess.check_output([
        "git","--no-replace-objects","-C",str(anyio_root),
        "show","1805944a9f6a062527c10aa044ded959782bfc3e:src/anyio/pytest_plugin.py"
    ])
    opcodes=difflib.SequenceMatcher(
        a=base.decode().splitlines(), b=generated.decode().splitlines()
    ).get_opcodes()
    changes=[row for row in opcodes if row[0]!="equal"]
    assert len(changes)==1 and changes[0][0]=="insert", changes
    assert changes[0][2]-changes[0][1]==0
    assert changes[0][4]-changes[0][3]==5, changes
    assert b"alexmojaki" not in generated

    payload={
        "schema":"UDM_G2_MUTABLE_CLOSURE_EQUIVALENCE_FIX_INDEPENDENT_QUALIFICATION_V2",
        "status":"PASS",
        "posthoc_training_repair":"WARRANTED_BOUNDED",
        "policy_selection":"EQUIVALENCE_CLASS",
        "policy_aliases_quotiented":36,
        "inserted_source_lines":5,
        "heldout_future":"UNOPENED",
        "G2":"UNKNOWN",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
    print("PASS_ANYIO_MUTABLE_CLOSURE_EQUIVALENCE_FIX_V2")
    print(json.dumps(payload,sort_keys=True))


if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: qualify_g2_anyio_mutable_closure_equivalence_fix_v2.py RESULT_ROOT ANYIO_ROOT OUT")
    main(*(Path(x).resolve() for x in sys.argv[1:]))
