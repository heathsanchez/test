"""Held-out transfer of existing source-native AST discovery.

Original PR authors provided code changes and tests. No repair generated.
"""
from pathlib import Path
import json, sys, hashlib
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/"external_pr_v1"))
import qualify as m

def main():
    spec_path=HERE/"FROZEN_PROTOCOL.json"
    spec=json.loads(spec_path.read_text())
    base=REPO.parent/"upstream-base"
    out=REPO.parent/"out"/"heldout-v2"
    out.mkdir(parents=True,exist_ok=True)
    if m.git(REPO,"hash-object","research/unified_consequence_runtime/external_pr_v1/qualify.py")!=spec["reused_qualifier_git_blob"]:
        raise ValueError("CHANGED_PREVIOUS_METHOD")
    m.verify_repo(base,spec["original_source_base"],spec["source_blob_before"],spec["original_test_blob_before"])
    original=(base/"tests/test_ieantn.py").read_text()
    rows=[]
    for item in spec["cases"]:
        number=item["pr"]
        head=REPO.parent/("upstream-pr"+str(number))
        metadata=json.loads((out/"metadata"/(str(number)+".json")).read_text())
        if (metadata.get("number")!=number or metadata.get("state")!="open"
            or metadata.get("head",{}).get("sha")!=item["head"]
            or metadata.get("base",{}).get("sha")!=spec["original_source_base"]):
            raise ValueError("PR_REVISION_MOVED")
        m.verify_repo(head,item["head"],item["source_blob"],item["test_blob"])
        fresh=m.discover_new_tests(original,(head/"tests/test_ieantn.py").read_text())
        workspace=out/str(number)
        before=m.prepare_overlay(workspace/"before",base/"scripts/ieantn.py",head/"tests/test_ieantn.py")
        after=m.prepare_overlay(workspace/"after",head/"scripts/ieantn.py",head/"tests/test_ieantn.py")
        if (before/"tests/test_ieantn.py").read_bytes()!=(after/"tests/test_ieantn.py").read_bytes():
            raise ValueError("DIFFERENT_TEST_INPUTS")
        a=m.run_unittest(before,fresh,90)
        b=m.run_unittest(after,fresh,90)
        old=m.run_full_suite(m.prepare_overlay(workspace/"old-full",
            base/"scripts/ieantn.py",base/"tests/test_ieantn.py"),90)
        new=m.run_full_suite(after,90)
        ok=(a["exit_code"] not in (0,124) and b["exit_code"]==0 and
            a["test_count"]==len(fresh)==b["test_count"] and
            old["exit_code"]==0 and new["exit_code"]==0 and
            new["test_count"]>=old["test_count"])
        rows.append({"pr":number,"head":item["head"],"new_tests":fresh,
          "before":a,"after":b,"old_suite":old,"new_suite":new,
          "verdict":"WARRANTED_BOUNDED_NATIVE_REGRESSION" if ok else "UNKNOWN",
          "fix_authored_by":"EXTERNAL_PR_AUTHOR","new_generator":"NOT_DEMONSTRATED"})
        print("PR_"+str(number)+(" PASS" if ok else " UNKNOWN"),flush=True)
    receipt={"schema":spec["schema"],"protocol_sha256":hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "old_method_git_blob":spec["reused_qualifier_git_blob"],"cases":rows,
        "qualified_count":sum(r["verdict"].startswith("WARRANTED") for r in rows),
        "generated_repair":False,"autonomous_generator_improvement":"UNKNOWN",
        "independent_outside_product_adoption":"UNKNOWN","app_installed":False}
    (out/"receipt.json").write_text(m.canonical(receipt))
    if receipt["qualified_count"]!=len(rows):
        raise ValueError("HELDOUT_TRANSFER_NOT_QUALIFIED")
    print("PASS_TWO_ADDITIONAL_SOURCE_NATIVE_PR_REPLAYS")
if __name__=="__main__":main()
