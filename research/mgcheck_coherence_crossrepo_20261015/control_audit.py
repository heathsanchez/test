#!/usr/bin/env python3
"""Run independent cold consumer, adversarial evidence and strong ledger controls."""
import hashlib,json,pathlib,subprocess,sys,time,os
HERE=pathlib.Path(__file__).resolve().parent
E=HERE/"evidence"
CONSUMER=HERE/"consumer.py"
def run():
    result=subprocess.run([sys.executable,str(CONSUMER),str(E)],capture_output=True,text=True,check=True)
    return json.loads(result.stdout)
def sha(b):return hashlib.sha256(b).hexdigest()
def native_ledger_reference():
    # Fully informed exact-executable ledger: same source/corpus and same
    # qualified A observation, no future acquisition. This is NOT an
    # unrun artificial model or a claim of strict MathGraph cost superiority.
    d={}
    for f in ("b","c"):
        old=json.loads((E/f"{f}_base.json").read_text())
        head=json.loads((E/f"{f}_head.json").read_text())
        keys={(x["program_index"],x["mode"]):x for x in old["results"]}
        newer={(x["program_index"],x["mode"]):x for x in head["results"]}
        r=sum(keys[k]["coherence"]=="VIOLATION" and newer[k]["coherence"]=="MATCH" for k in keys)
        d[f]={"qualified_repaired_count":r,"decision":"WARRANTED_BOUNDED_NATIVE_REPAIR_TRANSITIONS" if r else "UNKNOWN_NO_QUALIFIED_NATIVE_REPAIR_TRANSITION"}
    return d
def main():
    cap=E/"acquired_capability.json"
    origin=HERE/"acquired_capability_A_from_original_archive.json"
    original_cap=cap.read_bytes()
    original_origin=origin.read_bytes()
    b=E/"b_base.json"; original_b=b.read_bytes()
    normal=run();cold=run()
    if normal!=cold:raise SystemExit("COLD_REPLAY_NOT_DETERMINISTIC")
    if normal["families"]["b"]["qualified_repaired_count"]!=13 or normal["families"]["c"]["qualified_repaired_count"]!=0:
        raise SystemExit("UNEXPECTED_SCIENTIFIC_OUTCOME")
    if normal["families"]["c"]["decision"]!="UNKNOWN_NO_QUALIFIED_NATIVE_REPAIR_TRANSITION":
        raise SystemExit("FALSE_C_PROMOTION")
    try:
        cap.unlink()
        withdrawn=run()
        assert all(withdrawn["families"][f]["decision"]=="UNKNOWN_CAPABILITY_WITHDRAWN" for f in "bc")
        assert withdrawn["independent_native_controls_qualified"]
    finally:cap.write_bytes(original_cap)
    try:
        obj=json.loads(original_cap);obj["source_capability_sha256"]="0"*64
        cap.write_text(json.dumps(obj,sort_keys=True))
        invalid=run()
        assert all(invalid["families"][f]["decision"]=="UNKNOWN_CAPABILITY_SOURCE_REVOKED" for f in "bc")
    finally:cap.write_bytes(original_cap)
    try:
        origin.write_bytes(original_origin+b" ")
        rootmutated=run()
        assert all(rootmutated["families"][f]["decision"]=="UNKNOWN_ORIGIN" for f in "bc")
    finally:origin.write_bytes(original_origin)
    try:
        b.write_bytes(original_b+b" ")
        tampered=run()
        assert tampered["families"]["b"]["decision"]=="UNKNOWN_EVIDENCE_TAMPER"
        assert tampered["families"]["c"]["decision"]=="UNKNOWN_NO_QUALIFIED_NATIVE_REPAIR_TRANSITION"
    finally:b.write_bytes(original_b)
    final=run()
    if final!=normal:raise SystemExit("SOURCE_RESTORATION_FAILED")
    ledger=native_ledger_reference()
    tie=all(normal["families"][f]["qualified_repaired_count"]==ledger[f]["qualified_repaired_count"] and normal["families"][f]["decision"]==ledger[f]["decision"] for f in "bc")
    total_calls={"native_dump":0,"reference_tomllib_load":0,"native_reparse":0}
    native_ns=0
    for f in "bc":
        p=json.loads((E/"native_report.json").read_text())["families"][f]
        for rev,rows in p["native_calls_by_arm"].items():
            total_calls["native_dump"]+=rows["native_dumps"]
            total_calls["reference_tomllib_load"]+=rows["reference_parse"]
            total_calls["native_reparse"]+=rows["own_parse"]
            native_ns+=p["native_elapsed_ns_by_arm"][rev]
    out={
      "source_qualified_A_exact_bytes":sha(original_origin),
      "independent_receipt_cold_identical":cold==normal,
      "native_claims":normal["families"],
      "capability_withdrawal_typed_unknown_B_C":all(withdrawn["families"][f]["decision"]=="UNKNOWN_CAPABILITY_WITHDRAWN" for f in "bc"),
      "capability_root_digest_rejection":all(invalid["families"][f]["decision"]=="UNKNOWN_CAPABILITY_SOURCE_REVOKED" for f in "bc"),
      "origin_mutation_rejection":all(rootmutated["families"][f]["decision"]=="UNKNOWN_ORIGIN" for f in "bc"),
      "native_receipt_tamper_rejection":tampered["families"]["b"]["decision"]=="UNKNOWN_EVIDENCE_TAMPER",
      "independent_native_controls_survive_capability_withdrawal":withdrawn["independent_native_controls_qualified"],
      "exact_source_reinstatement_recovers_same_decisions":final==normal,
      "fully_informed_qualified_executable_ledger_replay":ledger,
      "ledger_parity_tie":tie,
      "ledger_additional_discovery_or_acquisition_calls":0,
      "native_observation_calls_across_original_base_head_and_ablation":total_calls,
      "native_python_instrumentation_seconds_including_programs":round(native_ns/1e9,6),
      "not_counted_in_native_seconds":["Git clone/setup","CI boot","Python installation","engineering/human construction","historical A acquisition/verifier work"],
      "overall_economic_superiority":"UNKNOWN; equally informed executable ledger ties; full lifetime costs unavailable",
      "two_independent_future_qualification":"UNKNOWN_NOT_BOTH",
      "strong_live_tool_using_coding_agent":"NOT_RUN",
      "epistemic_status":"WARRANTED_BOUNDED_ONE_SOURCE + REJECTED_TWO_SOURCE_FROZEN_GATE"
    }
    (E/"independent_control_audit.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k not in ("native_claims","fully_informed_qualified_executable_ledger_replay")},sort_keys=True))
    if not all((cold==normal,tie,withdrawn["independent_native_controls_qualified"],final==normal,out["native_receipt_tamper_rejection"])):
        raise SystemExit("INDEPENDENT_CONTROLS_FAILED")
if __name__=="__main__":main()
