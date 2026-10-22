#!/usr/bin/env python3
"""Separate post-exposure source change; original prospective V11 remains unchanged."""
import hashlib,importlib.util,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("v11_original",HERE/"experiment.py")
v11=importlib.util.module_from_spec(spec);spec.loader.exec_module(v11)
OUT=HERE/"postrun_requalification.json"
OLD="        name = name.lower()"
NEW="        name = bytes.lower(name)"
def main():
    original,author_test=v11.pins()
    assertions,_=v11.acquire_assertions(author_test)
    edited=original.replace(OLD,NEW,1)
    assert original.count(OLD)==1 and original!=edited
    assert edited.replace(NEW,OLD,1)==original
    before=hashlib.sha256(original.encode()).hexdigest()
    after=hashlib.sha256(edited.encode()).hexdigest()
    assert before!=after
    try:
        v11.SOURCE.write_text(edited)
        native=v11.separate_python("postexposure_bytes_lower",assertions)
        suite=v11.suite()
    finally:
        v11.SOURCE.write_text(original)
    n=native["receipt"]
    good=n.get("matches")==len(assertions) and suite["ok"]
    doc=v11.documentary_warrant(good)
    result={"status":"POSTEXPOSURE_REAL_SOURCE_PRESERVATION_PASS" if good else "POSTEXPOSURE_SOURCE_CHANGE_NOT_QUALIFIED",
      "baseline_source_sha256":before,"changed_source_sha256":after,
      "source_diff":"exact name.lower() to bytes.lower(name) within pinned normalized code",
      "source_changed":True,"new_source_identity_requalified":good,
      "old_authority_without_requalification":"UNKNOWN",
      "source_author_assertion_count":len(assertions),
      "native_extracted_witness":native,
      "unchanged_native_upstream_header_test":suite,
      "real_mathgraph_documentary_warrant":doc,
      "conventional_baseline":"upstream native header tests also PASS; no cost advantage",
      "scope":"ordinary controlled bytes; no proof for all subclasses or reflection",
      "original_prospective_V11":"unchanged, separately verified"}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"source_witness_matches":n.get("matches"),
       "tests_pass":suite["ok"],"old_authority":"UNKNOWN","new_source_warrant":doc["protected"]},sort_keys=True))
    if not good:raise RuntimeError("REAL_SOURCE_CHANGE_REQUALIFICATION_FAILED")
if __name__=="__main__":main()
