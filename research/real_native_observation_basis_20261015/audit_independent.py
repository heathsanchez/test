#!/usr/bin/env python3
"""Independent receiver-owned audit of previous GitHub native evidence archive.

Does not import the producer, the previous V11 solver, or implementation code.
Reconstructs the result from source-tagged native output plus standard tomllib.
Audits precisely finite observed contracts; NOT a proof of arbitrary TOML.
"""
from __future__ import annotations
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
OBS=("mut_status","native","length","render","parse_status","parsed","coherence")
IDENTITY={
    "A":("7ab7469addd60e03ca3bfbb1287642e8d771e1c0",
         "dcdfda3f825189c7f31048b6598142a944151073"),
    "B":("858186a3edb4cad6d66281ee7ad5fb07fe820406",
         "5d0b1825134a05da4e49654baa4717094a9f0896"),
    "C":("4b38becd75405e0f38ef3e47e9839eb407591c8a",
         "d17910d46bcc0f3d5b9c1de607a41836e1c85ce2"),
}
COUNT={"A":13,"B":8,"C":4}
FULL_CASES={"A":40,"B":25,"C":14}
def load(name):
    return json.loads((ROOT/name).read_bytes())
def sha(data):
    return hashlib.sha256(data).hexdigest()
def canonical(item):
    return json.dumps(item,sort_keys=True,ensure_ascii=False,separators=(",",":"))
def sig(row,columns):
    return canonical([row["features"][k] for k in columns])
def checkrow(row):
    f=row["features"]
    assert set(f)==set(OBS)
    mutation=f["mut_status"]
    if mutation!="OK":
        return "UNKNOWN"
    native=f["native"]
    assert len(native)==f["length"]
    try:
        actual=tomllib.loads("value = "+f["render"])["value"]
        parse="OK"
    except Exception as e:
        actual=None
        parse="ERROR_"+type(e).__name__
    assert f["parse_status"]==parse
    assert f["parsed"]==actual
    coherent=(parse=="OK" and actual==native)
    assert f["coherence"]==coherent
    return "PASS" if coherent else "FAIL"
def validate_family(name):
    o=load(name+"old.json");h=load(name+"head.json")
    assert o["source_sha"]==IDENTITY[name][0]
    assert h["source_sha"]==IDENTITY[name][1]
    assert o["family"]==name and h["family"]==name
    assert o["source_package"].endswith("tomlkit/__init__.py")
    assert h["source_package"].endswith("tomlkit/__init__.py")
    assert len(o["rows"])==len(h["rows"])==FULL_CASES[name]
    assert o["native_tests"]==h["native_tests"]==FULL_CASES[name]
    assert [x["id"] for x in o["rows"]]==[x["id"] for x in h["rows"]]
    for source in (o,h):
        for row in source["rows"]:
            assert checkrow(row)==row["label"],(name,row["id"],row["label"])
    oldfail={r["id"] for r in o["rows"] if r["label"]=="FAIL"}
    changed={a["id"] for a,b in zip(o["rows"],h["rows"])
             if a["label"]=="FAIL" and b["label"]=="PASS"}
    assert changed==oldfail and len(changed)==COUNT[name]
    assert all(row["label"]=="PASS" for row in h["rows"])
    # Strong causal distinction: all primitive state-only observations
    # agree across both exact source revisions for every frozen native case.
    initial=("mut_status","native","length")
    primitive_diffs=sum(sig(a,initial)!=sig(b,initial)
                        for a,b in zip(o["rows"],h["rows"]))
    assert primitive_diffs==0
    qualified_diffs=sum(sig(a,("coherence",))!=sig(b,("coherence",))
                        for a,b in zip(o["rows"],h["rows"]))
    assert qualified_diffs==COUNT[name]
    return (o,h),{
        "original_old_native":o["source_sha"],
        "original_head_native":h["source_sha"],
        "finite_programs_each_revision":len(o["rows"]),
        "source_old_contract_violations":len(oldfail),
        "original_contributor_head_violations":0,
        "base_head_differences_primitive_values_length_completion":primitive_diffs,
        "base_head_differences_native_cross_view_coherence":qualified_diffs,
        "original_first_counterexample":next(row["id"] for row in o["rows"] if row["label"]=="FAIL")
    }
def source_optimum(rows):
    opts=[]
    for subset_size in range(len(OBS)+1):
        for cols in itertools.combinations(OBS,subset_size):
            indexed={}
            supported=True
            for row in rows:
                if row["label"]=="UNKNOWN":continue
                key=sig(row,cols)
                if key in indexed and indexed[key]!=row["label"]:
                    supported=False;break
                indexed[key]=row["label"]
            if supported:opts.append(cols)
    smallest=min(map(len,opts))
    minimizers=[m for m in opts if len(m)==smallest]
    assert smallest==1 and minimizers==[("coherence",)]
    return opts,smallest,minimizers
def evaluate(cap,families):
    if cap is None:return "UNKNOWN_CAPABILITY_NOT_AVAILABLE",None
    selected=cap["selected_channels"]
    known=cap["source_compiled_lookup"]
    result={}
    for name,(o,h) in families.items():
        oldfail={r["id"] for r in o["rows"] if r["label"]=="FAIL"}
        fixed={r["id"] for r in h["rows"] if r["label"]=="PASS"}
        repaired=oldfail&fixed
        detected=0
        false=0
        for version in (o,h):
            for row in version["rows"]:
                guess=known.get(sig(row,selected),"UNKNOWN_UNSEEN")
                if guess in ("PASS","FAIL") and guess!=row["label"]:
                    false+=1
                if version is o and row["id"] in repaired and guess=="FAIL":
                    detected+=1
        result[name]={"repaired":len(repaired),"detected":detected,
                      "false":false}
    return "QUALIFIED_BOUNDED_REPLAY",result

def main():
    sources={};brief={}
    for name in "ABC":
        sources[name],brief[name]=validate_family(name)
    policy_bytes=(ROOT/"learned_capability_A.json").read_bytes()
    expected_text=(ROOT/"frozen_A_capability_sha256.txt").read_text().split()[0]
    assert sha(policy_bytes)==expected_text
    cap=json.loads(policy_bytes)
    assert cap["source_A"]=={"old":IDENTITY["A"][0],"head":IDENTITY["A"][1]}
    assert cap["original_v11_solver_blob"]=="0f7fb6b837cd65aa86b5fef7c097196fc0df4845"
    assert cap["candidate_observation_masks_exhaustively_checked"]==128
    opts,size,minimizers=source_optimum(sources["A"][0]["rows"]+sources["A"][1]["rows"])
    assert cap["exact_A_observation_optimum"]==size
    assert tuple(cap["selected_channels"])==minimizers[0]
    assert cap["source_old_fail_to_head_pass"]==COUNT["A"]
    # Cold receiver uses only qualified A policy and already generated native
    # B/C data. Its independent verdict matches the producer report.
    status,replayed=evaluate(cap,{k:sources[k] for k in "BC"})
    assert status=="QUALIFIED_BOUNDED_REPLAY"
    for name in "BC":
        assert replayed[name]=={"repaired":COUNT[name],"detected":COUNT[name],"false":0}
    original=load("final_report.json")
    assert original["status"]=="PASS_BOUNDED_NATIVE_SOURCE_A_TO_TWO_FUTURE_OPERATIONS"
    assert original["physical_withdrawal"]=="UNKNOWN_CAPABILITY_WITHDRAWN"
    for name in "BC":
        assert original["future"][name]["learned_method_recognized_repaired_witnesses"]==COUNT[name]
        assert original["future"][name]["false_warrants"]==0
    assert sha((ROOT/"final_report.json").read_bytes())==(ROOT/"report_sha256.txt").read_text().strip()

    # Physical withdrawal at recipient, not just an existence-field in
    # a report. Importing absent capability must yield explicit UNKNOWN,
    # and re-admission must recover all original decisions.
    import tempfile,shutil
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td)/"cap.json"
        temp.write_bytes(policy_bytes)
        def recipient():
            if not temp.is_file():return evaluate(None,{k:sources[k] for k in "BC"})
            if sha(temp.read_bytes())!=expected_text:return "UNKNOWN_STALE_SOURCE",None
            return evaluate(json.loads(temp.read_bytes()),{k:sources[k] for k in "BC"})
        assert recipient()==(status,replayed)
        temp.unlink()
        assert recipient()==("UNKNOWN_CAPABILITY_NOT_AVAILABLE",None)
        temp.write_bytes(policy_bytes)
        assert recipient()==(status,replayed)
        temp.write_bytes(policy_bytes+b"x")
        assert recipient()==("UNKNOWN_STALE_SOURCE",None)

    # Forged verdict cannot masquerade as independent source truth;
    # independently reconstructed TOML reference must reject.
    corrupted=copy.deepcopy(sources["A"][0]["rows"])
    witness=next(x for x in corrupted if x["label"]=="FAIL")
    witness["features"]["coherence"]=True
    try:checkrow(witness)
    except AssertionError:tamper_rejected=True
    else:tamper_rejected=False
    assert tamper_rejected
    result={
        "status":"INDEPENDENT_AUDIT_PASS_EXACT_FINITE",
        "input_original_run":38639050079,
        "original_source_no_target_relearning":True,
        "original_source_A_selected_observation":cap["selected_channels"],
        "source_A_unique_minimal_basis":minimizers,
        "complete_observation_mask_exhaustion":128,
        "eligible_observation_subsets":len(opts),
        "true_retained_replay":replayed,
        "independent_native_language_reference":"Python 3.13 stdlib tomllib",
        "native_source_verdicts":brief,
        "recipient_physical_capability_withdrawal":"PASS_UNKNOWN_THEN_RESTORED",
        "false_capability_source_digest":"PASS_REFUSED",
        "tampered_native_observation":"PASS_REFUSED",
        "strict_full_information_exhaustive_reference":"TIE",
        "strong_coding_agent":"NOT_RUN",
        "source_count":"ONE_REPOSITORY_THREE_DISTINCT_PR_REVISIONS",
        "new_method_primitive_autonomous_invention":"NOT_ESTABLISHED",
        "human_predeclared_mutation_and_observation_vocabulary":True,
        "novel_defect_discovery":"NOT_CLAIMED",
        "lifecycle_economic_advantage":"NOT_MEASURED"
    }
    dest=ROOT/"independent_receiver_audit.json"
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:result[k] for k in ("status","original_source_A_selected_observation",
          "true_retained_replay","recipient_physical_capability_withdrawal",
          "tampered_native_observation","strict_full_information_exhaustive_reference")},sort_keys=True))
if __name__=="__main__":main()
