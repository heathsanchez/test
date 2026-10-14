#!/usr/bin/env python3
"""Independent all-corpus YAML string-roundtrip replay. No upstream changes."""
import argparse, hashlib, importlib.metadata, json, os, pathlib, platform, sys
import yaml

ORIGINAL=pathlib.Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-roundtrip-native-receipts"
OUT=pathlib.Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-triple-oracle-20261015"
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED_SHA="86b3b2477024dec6cb57b82c3503d472132c5b50f2214bc34aa03afccfc8f2fe"
PINS={
    "goccy/go-yaml":"72a4f95c648c844ef2f8ddbc009530be64ab4c41",
    "go-yaml/yaml":"944c86a7d29391925ed6ac33bee98a0516f1287a"
}
def verified_data():
    corpus_path=ORIGINAL/"mathgraph_roundtrip_corpus.json"
    manifest_path=ORIGINAL/"REPORT.json"
    data=corpus_path.read_bytes()
    sha=hashlib.sha256(data).hexdigest()
    assert sha==EXPECTED_SHA,("CORPUS_HASH_MISMATCH",sha)
    cases=json.loads(data)
    assert len(cases)==1088 and len({x["id"] for x in cases})==1088
    old=json.loads(manifest_path.read_text())
    assert old["case_corpus_sha256"]==sha
    assert len(old["repos"])==2
    for item in old["repos"]:
        assert item["repo"] in PINS and item["sha"]==PINS[item["repo"]]
        assert item["cases"]==1088
    by_repo={x["repo"]:x for x in old["repos"]}
    tar=set(by_repo["goccy/go-yaml"]["failed_ids"])
    ref=set(by_repo["go-yaml/yaml"]["failed_ids"])
    assert (len(tar),len(ref),len(tar-ref),len(tar&ref),len(ref-tar))==(21,15,16,5,10), "NATIVE_DRIFT_FROM_FROZEN_DISCOVERY"
    assert len(old["candidate_target_only"])==16
    assert {x["id"] for x in old["candidate_target_only"]}==tar-ref
    return sha,cases,old,tar,ref
def native_third(cases):
    outcomes={}
    for c in cases:
        v=c["value"]
        try:
            emitted=yaml.safe_dump({"value":v},allow_unicode=True,sort_keys=True)
            decoded=yaml.safe_load(emitted)
            if not isinstance(decoded,dict):
                status="NON_MAPPING"
                actual_type=type(decoded).__name__
                actual=repr(decoded)
            elif "value" not in decoded:
                status="MISSING_VALUE"
                actual_type="missing"
                actual="<missing>"
            else:
                got=decoded["value"]
                actual_type=type(got).__name__
                actual=repr(got)
                status=("PASS_EXACT_STRING" if type(got) is str and got==v else "DIFFERENT")
            outcomes[c["id"]]={"status":status,"type":actual_type,
                "actual_repr":actual[:500],
                "emitted_yaml":emitted if status!="PASS_EXACT_STRING" else None}
        except Exception as e:
            outcomes[c["id"]]={"status":"UNKNOWN_EXCEPTION","error":type(e).__name__+":"+str(e)[:300]}
    return outcomes
def run(mode):
    sha,cases,old,tar,ref=verified_data()
    py=native_third(cases)
    assert len(py)==1088
    corpus={c["id"]:c for c in cases}
    pypass={k for k,v in py.items() if v["status"]=="PASS_EXACT_STRING"}
    pyfail=set(py)-pypass
    targetonly=tar-ref
    corroborated=sorted(targetonly&pypass)
    conflict=sorted(targetonly-pypass)
    thirdalone=sorted(pyfail-(tar|ref))
    # Native Go failure alone warrants exact internal roundtrip violation;
    # PyYAML contributes a separately implemented corroborating comparison.
    status=("CORROBORATED_BOUNDED_STRING_ROUNDTRIP_WITNESSES"
        if corroborated else "UNKNOWN_THIRD_ORACLE_CONFLICT")
    if mode=="ablate-third":status="UNKNOWN_REFERENCE_REMOVED"
    elif mode=="withdraw":status="STALE_EVIDENCE_WITHDRAWN"
    elif mode!="original":raise ValueError("bad mode")
    report={
        "protocol":"research/mathgraph_roundtrip_triple_oracle_20261015/FROZEN_PROTOCOL.md",
        "mode":mode,"result":status,
        "original_pins":PINS,"original_corpus_sha256":sha,
        "third_version":"PyYAML=="+importlib.metadata.version("PyYAML"),
        "python":platform.python_version(),
        "counts":{"cases":len(cases),"old_target_native_fail":len(tar),
                  "old_go_reference_native_fail":len(ref),
                  "old_target_only":len(targetonly),
                  "pyyaml_fail_or_unsupported":len(pyfail),
                  "target_only_corrobated_by_py_yaml":len(corroborated),
                  "target_only_py_yaml_conflict":len(conflict),
                  "py_yaml_failure_not_seen_in_go":len(thirdalone)},
        "corroborated":[{"id":k,"input":corpus[k],"py_yaml":py[k]} for k in corroborated] if mode=="original" else [],
        "conflicts":[{"id":k,"input":corpus[k],"py_yaml":py[k]} for k in conflict] if mode=="original" else [],
        "py_yaml_only":[{"id":k,"input":corpus[k],"py_yaml":py[k]} for k in thirdalone[:30]] if mode=="original" else [],
        "negative_controls":{"independent_third_removed_fail_closed":mode=="ablate-third",
                             "withdrawal_preserves_old_evidence_but_no_current_warrant":mode=="withdraw"},
        "limitations":["Not new blind discovery: prior original candidate inputs already known",
                       "Invariant only: exact map[string]any string roundtrip, not complete YAML specification",
                       "No new program/assertion invention, no L7, no external user adoption",
                       "No claims of improvement over a conventional fully-informed baseline"],
        "action_authority":"NONE"
    }
    f=OUT/(mode+".json")
    f.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("MATHGRAPH_THREE_WAY_ORACLE "+json.dumps(
        {"mode":mode,"result":status,"counts":report["counts"],
         "first_corroborated":[{"id":k,"value":corpus[k]["value"]} for k in corroborated[:8]],
         "third":"PyYAML=="+importlib.metadata.version("PyYAML"),
         "full_receipt":str(f)},ensure_ascii=False),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["original","ablate-third","withdraw"],default="original")
    args=p.parse_args()
    run(args.mode)
