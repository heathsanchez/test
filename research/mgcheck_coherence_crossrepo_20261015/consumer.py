#!/usr/bin/env python3
"""Independent bounded receipt consumer: source-attested, withdrawable, restartable."""
import hashlib, json, pathlib, sys, time
ORIGIN_SHA = "2407927cfc0a7b5061aefecce70ae69ddd19a70820883d08439da5fb2aa363d1"
A_ZIP_SHA = "2ab47701fa213e417b528ccd2e46a9233143c9b5191bd2c5aea112a24412d057"
SOURCES = {
 "b":{"base":"1cc59b351e1ff5c7591ab05d4d027638100af82b","head":"5be7c5041f28df68365ec4f3d77b3363ede198be"},
 "c":{"base":"d883c7cf2ae48eae5ba572c1d45bc46fbf8e5cb5","head":"b28b705bd364aa7d7fbc9f6102bca3ceda223dbf"}
}
def raw(p):return pathlib.Path(p).read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def load(p):return json.loads(raw(p))
def assess(root, E):
    independent={"native_control":"UNKNOWN","source_bound":False}
    rootA=root/"acquired_capability_A_from_original_archive.json"
    receipt=E/"acquired_capability.json"
    try:
        if sha(rootA)!=ORIGIN_SHA: raise ValueError("ORIGIN_BYTES_MISMATCH")
        origin=load(rootA)
        if origin["selected_channels"]!=["coherence"]:raise ValueError("ORIGIN_OPERATOR_INVALID")
        source={"readable":True,"digest":ORIGIN_SHA}
    except Exception as ex:
        source={"readable":False,"error":str(ex)[:150]}
    cap_status="READY"
    if not receipt.exists():cap_status="UNKNOWN_CAPABILITY_WITHDRAWN"
    elif not source["readable"]:cap_status="UNKNOWN_ORIGIN"
    else:
        try:
            cap=load(receipt)
            if cap["observation"]!="coherence" or cap["source_capability_sha256"]!=ORIGIN_SHA or cap["source_archive_sha256"]!=A_ZIP_SHA:
                cap_status="UNKNOWN_CAPABILITY_SOURCE_REVOKED"
        except Exception:cap_status="UNKNOWN_CORRUPT_CAPABILITY"
    result={"origin":source,"capability_state":cap_status,"families":{}}
    prev=load(E/"native_report.json")
    for f in ("b","c"):
        p=prev["families"][f]
        controls=0;err=None;repairs=[];resets=[];fail_closed=False
        try:
            reports={rev:load(E/f"{f}_{rev}.json") for rev in ("base","head","ablated")}
            for rev in reports:
                if sha(E/f"{f}_{rev}.json")!=p["raw_native_json_sha256"][rev]:raise ValueError("NATIVE_REPORT_TAMPER")
            if reports["base"]["source_sha"]!=SOURCES[f]["base"] or reports["head"]["source_sha"]!=SOURCES[f]["head"]:
                raise ValueError("WRONG_NATIVE_GIT_SHA")
            def index(r):return {(x["program_index"],x["mode"]):x for x in r["results"]}
            old=index(reports["base"]);new=index(reports["head"]);off=index(reports["ablated"])
            if old.keys()!=new.keys() or new.keys()!=off.keys():raise ValueError("MISMATCHED_CASES")
            controls=sum(old[k]["coherence"]=="MATCH" and new[k]["coherence"]=="MATCH" for k in old)
            repairs=[repr(k) for k in old if old[k]["coherence"]=="VIOLATION" and new[k]["coherence"]=="MATCH"]
            resets=[repr(k) for k in old if old[k]["coherence"]=="VIOLATION" and new[k]["coherence"]=="MATCH" and off[k]["coherence"]=="VIOLATION" and off[k].get("reference_canonical")==old[k].get("reference_canonical")]
            if len(resets)!=len(repairs):raise ValueError("ABLATED_SOURCE_NOT_CAUSAL")
            if p["fixed_native_witness_count"]!=len(repairs):raise ValueError("CLAIM_INFLATION")
        except Exception as ex:
            err=str(ex)[:150];fail_closed=True
        if fail_closed:verdict="UNKNOWN_EVIDENCE_TAMPER"
        elif cap_status!="READY":verdict=cap_status
        elif repairs:verdict="WARRANTED_BOUNDED_NATIVE_REPAIR_TRANSITIONS"
        else:verdict="UNKNOWN_NO_QUALIFIED_NATIVE_REPAIR_TRANSITION"
        result["families"][f]={"decision":verdict,"qualified_repaired_count":len(repairs) if verdict.startswith("WARRANTED_") else 0,"raw_repaired_count":len(repairs),"ablated_restored_count":len(resets),"unrelated_native_positive_controls":controls,"error":err}
    # Native positive controls depend on their own original source and oracle,
    # not on A learned capability. Preserve them upon capability withdrawal.
    result["independent_native_controls_qualified"]=all(result["families"][f]["unrelated_native_positive_controls"]>0 and result["families"][f]["error"] is None for f in ("b","c"))
    return result
def main():
    E=pathlib.Path(sys.argv[1]).resolve(); root=E.parent
    print(json.dumps(assess(root,E),sort_keys=True,indent=2))
if __name__=="__main__":main()
