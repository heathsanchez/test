#!/usr/bin/env python3
"""Frozen cross-domain prospective failure test and actual informed native baseline."""
import base64,binascii,datetime,hashlib,importlib.util,json,pathlib,re,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
READER=ROOT/"structural_obligation_ir_v1"/"experiment.py"
DEONTIC=ROOT/"deontic_obligation_v4"/"experiment.py"
V5=ROOT/"obligation_to_native_witness_v5"/"experiment.py"
URL="https://docs.python.org/3/library/base64.html"
TARGET=("base64","validate","validation","non-alphabet","character","error","reject")
OUT=pathlib.Path(__file__).with_name("result.json")
def imported(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
def count_target(text):
    words=set(re.findall(r"[a-z]+",text.lower()))
    return sum(x in text.lower() if "-" in x else x in words for x in TARGET)
def freeze_candidate(doc, structural, deontic, v5):
    ps=structural.paragraphs(doc)
    candidates=[]
    for i,p in enumerate(ps):
        src={"url":URL,"paragraph_index":i}
        structural_relation=structural.structural_ir(p,src)
        if structural_relation["status"]=="STRUCTURAL_IR":
            candidates.append({"index":i,"kind":"STRUCTURAL","score":count_target(p),
                               "ir":structural_relation})
        for ir in deontic.deontic_ir(p,src):
            candidates.append({"index":i,"kind":"DEONTIC","score":count_target(p),
                               "ir":ir})
    candidates.sort(key=lambda x:(-x["score"],x["index"],x["kind"]))
    selected=candidates[0] if candidates else None
    if selected is None or selected["score"]<2:
        return {"status":"UNKNOWN_NO_TARGET_RELEVANT_SOURCE_IR"},selected,len(candidates)
    # Reuse the V5 safe SQL witness builder on unchanged deontic shape;
    # structural relations are unsupported, no improvised Python adapter.
    if selected["kind"]!="DEONTIC":
        return {"status":"UNKNOWN_NO_DEONTIC_TO_NATIVE_ADAPTER"},selected,len(candidates)
    frozen_item={"score":selected["score"],"ir":selected["ir"]}
    try:
        program=v5.compile_program(frozen_item)
    except (ValueError,KeyError,TypeError) as exc:
        program={"status":"UNKNOWN_COMPILER_TYPE_MISMATCH","error_type":type(exc).__name__}
    if program.get("status")=="ADMISSIBLE_DDL_WITNESS":
        # This would be an unrelated family; reject false positives.
        return {"status":"FALSE_TOPIC_SQL_WITNESS_FOR_BASE64"},selected,len(candidates)
    return program,selected,len(candidates)
def baseline():
    # Controlled native library calls, not derived by candidate algorithm.
    outcome={}
    try:
        base64.b64decode(b"!!!!",validate=True)
        outcome["strict"]="ACCEPT"
    except binascii.Error:
        outcome["strict"]="REJECT"
    try:
        b=base64.b64decode(b"!!!!",validate=False)
        outcome["lenient"]={"status":"ACCEPT","value_hex":b.hex()}
    except binascii.Error:
        outcome["lenient"]={"status":"REJECT"}
    outcome["distinguishes"]=outcome["strict"]=="REJECT" and outcome["lenient"]=={"status":"ACCEPT","value_hex":""}
    outcome["function_calls"]=2
    return outcome
def main():
    structural=imported(READER,"frozen_ir_v1")
    deontic=imported(DEONTIC,"frozen_deontic_v4")
    v5=imported(V5,"frozen_witness_v5")
    req=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-Cross-Domain-Witness-V6/1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(2_000_001); final=r.geturl()
    if final!=URL or len(raw)>2_000_000:raise RuntimeError("SOURCE_INTEGRITY_FAILURE")
    body=raw.decode("utf-8")
    topic=(("validate" in body.lower()) and ("binascii.error" in body.lower() or
                                             "binascii" in body.lower()))
    if topic:
        candidate,selected,counts=freeze_candidate(body,structural,deontic,v5)
        comparator=baseline()
        verdict="CANDIDATE_TRANSFER" if candidate.get("status")=="ADMISSIBLE_NATIVE_WITNESS" else "REJECTED_CROSS_DOMAIN_WITNESS_TRANSFER"
    else:
        candidate={"status":"UNKNOWN_SOURCE_TARGET_INAPPLICABLE"}
        selected=None;counts=0;comparator={"status":"NOT_SCORED"};verdict="UNKNOWN_SOURCE_TARGET_INAPPLICABLE"
    report={"source":URL,"retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_sha256":hashlib.sha256(raw).hexdigest(),"source_bytes":len(raw),
            "source_topic_exists":topic,"relevant_ir_count":counts,"selected_ir":selected,
            "candidate":candidate,"native_comparator":comparator,"verdict":verdict,
            "baseline_cost":"2 native calls; no lifecycle time/money measured",
            "semantic_prior":"challenge topic and baseline behavior anticipated before retrieval; candidate no base64 adapter",
            "R7_CLC_MATHGRAPH":"UNCHANGED_NOT_EXECUTED"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"source_sha256":report["source_sha256"],"topic":topic,
         "candidate":candidate,"comparator":comparator,"verdict":verdict},sort_keys=True))
    if topic and not comparator.get("distinguishes",False):
        raise AssertionError("INDEPENDENT_BASELINE_NATIVE_OUTCOME_DIFFERED")
if __name__=="__main__":main()
