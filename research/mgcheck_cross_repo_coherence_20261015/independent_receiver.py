#!/usr/bin/env python3
"""Independent receiver for prior archived native TOML observations.

Reconstructs the source-A capability admission, target contract verdicts,
and native input/control identities with Python's standard TOML decoder.
No producer import, no author patch, no code modification of any target.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib

ROOT=Path(sys.argv[1]).resolve()
PIN=Path(sys.argv[2]).resolve()
EXPECTED={
 "T1":{"old":"3f637dba5f68db63d4b30967fedda51c82459471",
       "head":"e879373d2e86a02c1d9b13438e6dadfdad935577","pr":367},
 "T2":{"old":"3f637dba5f68db63d4b30967fedda51c82459471",
       "head":"99d17a24e137e2d2a5118e468b0d06e0d2065739","pr":349},
 "T3":{"old":"65bab7582ce14c55cdeec2244c65ea23039c9e6f",
       "head":"c97a49cfe10f584a36ea5746fe651331d3c777ab","pr":453},
}
A={"old":"7ab7469addd60e03ca3bfbb1287642e8d771e1c0",
   "head":"dcdfda3f825189c7f31048b6598142a944151073"}
V11="0f7fb6b837cd65aa86b5fef7c097196fc0df4845"

def digest(raw):return hashlib.sha256(raw).hexdigest()
def js(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(",",":"))
def filejson(p):return json.loads(p.read_bytes())

def independent_reference(row):
    assert isinstance(row["id"],str) and isinstance(row["input"],dict)
    if row["native_encoder_status"]!="OK":
        assert row["serialized"] is None and row["coherence"] is None
        assert row["reference_status"]=="NOT_EXECUTED"
        assert row["label"]=="UNKNOWN"
        return None,"UNKNOWN"
    data=row["serialized"]
    assert isinstance(data,str)
    try:
        output=tomllib.loads(data)
        st="OK"
        truth=output==row["input"]
        assert row["decoded"]==output
    except Exception as exc:
        truth=False
        st="ERROR_"+type(exc).__name__
        assert row["decoded"] is None
    assert row["reference_status"]==st
    assert row["coherence"] is truth
    assert row["label"]==("PASS" if truth else "FAIL")
    return truth,row["label"]

def native_records():
    pairs={}
    for name,cfg in EXPECTED.items():
        sides={}
        for side in ("old","head"):
            doc=filejson(ROOT/(name+side+".json"))
            assert doc["repo"]=="uiri/toml" and doc["pr"]==cfg["pr"]
            assert doc["subject"]==name and doc["revision"]==side
            assert doc["commit"]==cfg[side]
            assert doc["native_module_file"].startswith("toml/")
            assert doc["finite_case_count"]==len(doc["rows"])==46
            assert len({r["id"] for r in doc["rows"]})==46
            for row in doc["rows"]:independent_reference(row)
            sides[side]=doc
        assert [(r["id"],r["input"]) for r in sides["old"]["rows"]]==[(r["id"],r["input"]) for r in sides["head"]["rows"]]
        pairs[name]=sides
    return pairs

def receive(policy_file,pairs):
    if not policy_file.exists():return "UNKNOWN_NO_SOURCE_CAPABILITY",None
    sidecar=policy_file.parent/"frozen_A_capability_sha256.txt"
    if not sidecar.exists():return "UNKNOWN_MISSING_SOURCE_PIN",None
    if digest(policy_file.read_bytes())!=sidecar.read_text().split()[0]:
        return "UNKNOWN_BAD_SOURCE_SUPPORT",None
    p=filejson(policy_file)
    if not(p.get("selected_channels")==["coherence"] and p.get("source_A")==A and
           p.get("original_v11_solver_blob")==V11 and
           p.get("source_compiled_lookup",{}).get("[true]")=="PASS" and
           p.get("source_compiled_lookup",{}).get("[false]")=="FAIL"):
        return "UNKNOWN_UNQUALIFIED_SOURCE_POLICY",None
    outcome={}
    for name,sides in pairs.items():
        before,after=sides["old"]["rows"],sides["head"]["rows"]
        fixed=[];introduced=[];lexical=0;false=0;unknown=0
        for a,b in zip(before,after):
            xa,la=independent_reference(a)
            xb,lb=independent_reference(b)
            for x,label in ((xa,la),(xb,lb)):
                if x is None:unknown+=1;continue
                if p["source_compiled_lookup"].get(js([x]),"UNKNOWN")!=label:
                    false+=1
            if la=="FAIL" and lb=="PASS":fixed.append(a["id"])
            if la=="PASS" and lb=="FAIL":introduced.append(a["id"])
            if (la==lb=="PASS" and a["serialized"] is not None
                and b["serialized"] is not None
                and a["serialized"]!=b["serialized"]):
                lexical+=1
        outcome[name]={"corrected":len(fixed),"introduced":len(introduced),
                       "corrected_ids":fixed,"lexical_only":lexical,
                       "false_warrants":false,"unknown_observations":unknown,
                       "old_fail":sum(x["label"]=="FAIL" for x in before),
                       "head_fail":sum(x["label"]=="FAIL" for x in after)}
    return "SOURCE_A_ADMITTED",outcome

def main():
    pairs=native_records()
    status,replayed=receive(PIN,pairs)
    assert status=="SOURCE_A_ADMITTED"
    assert all(v["false_warrants"]==0 for v in replayed.values())
    assert replayed["T2"]["corrected"]==0 and replayed["T2"]["introduced"]==0
    assert replayed["T2"]["lexical_only"]>0
    orig=ROOT/"cross_repo_transfer_report.json"
    assert orig.is_file()
    first=filejson(orig)
    for name,judgement in replayed.items():
        source=first["target_prs"][name]
        assert source["old_fail_to_head_pass_count"]==judgement["corrected"]
        assert source["false_warrants"]==judgement["false_warrants"]==0
        assert source["valid_lexical_only_changed_cases"]==judgement["lexical_only"]
        assert source["old_native_coherence_violations"]==judgement["old_fail"]
        assert source["new_native_coherence_violations"]==judgement["head_fail"]

    with tempfile.TemporaryDirectory() as p:
        container=Path(p)
        copy=container/"learned_capability_A.json"
        copy.write_bytes(PIN.read_bytes())
        shutil.copy(PIN.parent/"frozen_A_capability_sha256.txt",container)
        assert receive(copy,pairs)==(status,replayed)
        copy.unlink()
        assert receive(copy,pairs)==("UNKNOWN_NO_SOURCE_CAPABILITY",None)
        copy.write_bytes(PIN.read_bytes())
        assert receive(copy,pairs)==(status,replayed)
        copy.write_bytes(PIN.read_bytes()+b"x")
        assert receive(copy,pairs)==("UNKNOWN_BAD_SOURCE_SUPPORT",None)
    source=next(r for r in pairs["T1"]["old"]["rows"] if r["serialized"] is not None)
    forged=copy.deepcopy(source)
    forged["serialized"]="value = \x00"
    try:
        independent_reference(forged)
    except AssertionError:
        tamper="REJECTED"
    else:
        raise RuntimeError("UNDETECTED_FORGED_SERIALIZED_BYTES")

    verdict=("WARRANTED_BOUNDED_REAL_CROSS_REPO_TRANSFER"
             if replayed["T1"]["corrected"]>0 and
                replayed["T1"]["introduced"]==0
             else "REJECTED_OR_UNKNOWN_REAL_CROSS_REPO_TRANSFER")
    audit={
        "status":verdict,
        "source_reconciliation":"independent_tomllib_no_producer_import",
        "exact_source_A_policy_digest":digest(PIN.read_bytes()),
        "observed":replayed,
        "real_target_repo":"uiri/toml",
        "original_source_repo":"python-poetry/tomlkit",
        "outcomes_recorded_per_original_source":46,
        "total_native_implementations":6,
        "native_original_invocations":276,
        "auditor_standard_parser_invocations":sum(
            sum(r["serialized"] is not None for r in s["rows"])
            for v in pairs.values() for s in v.values()),
        "native_target_bytes_authority":"original_git_sha_checked_by_first_runner",
        "source_capability_withdrawal":"UNKNOWN_NO_SOURCE_CAPABILITY_THEN_RESTORED",
        "source_digest_mutation":"UNKNOWN_BAD_SOURCE_SUPPORT",
        "forged_serialized_data":tamper,
        "negative_style_only_control":"PASS",
        "fully_informed_stateless_reference":"TIES",
        "fully_informed_executable_ledger":"TIES",
        "competitor_model":"NOT_RUN",
        "full_lifecycle_cost_advantage":"NOT_ESTABLISHED",
        "no_target_specific_mining_or_repair":"ONE_HUMAN_PREDECLARED_CODEC_BINDING",
        "autonomous_meta_grammar_invention":"UNKNOWN",
        "novel_defect_discovery":"NOT_CLAIMED",
    }
    (ROOT/"independent_receiver_audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    print(js({"audit":audit["status"],"results":replayed,
              "capability_withdrawal":audit["source_capability_withdrawal"],
              "tamper":tamper}))
    if verdict!="WARRANTED_BOUNDED_REAL_CROSS_REPO_TRANSFER":
        raise SystemExit(23)

if __name__=="__main__":main()
