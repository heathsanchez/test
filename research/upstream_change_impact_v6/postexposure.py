#!/usr/bin/env python3
"""Post-exposure control on exactly exposed multiline MarkupSafe _native.py.

Original prospective inapplicability remains unchanged in result.json.
"""
import hashlib,json,os,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
SRC=UP/"src/markupsafe/_native.py"
PIN="4e111271b1494995708a9e878a10829b5e10c7ba"
OUT=HERE/"postexposure_result.json"
def exec_case(args):
    t=time.perf_counter()
    env=os.environ.copy();env["PYTHONPATH"]=str(UP/"src")
    p=subprocess.run(args,cwd=UP,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,timeout=180)
    return {"ok":p.returncode==0,"returncode":p.returncode,
        "seconds":round(time.perf_counter()-t,6),
        "tail":p.stdout.strip().splitlines()[-8:]}
def direct_probe():
    return exec_case([sys.executable,"-c",
         "from markupsafe._native import _escape_inner;"
         "assert _escape_inner(\"&><'\\\"\") == \"&amp;&gt;&lt;&#39;&#34;\";"
         "assert _escape_inner('plain')=='plain'"])
def all_tests():
    return exec_case([sys.executable,"-m","pytest","-q","tests"])
def main():
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=UP,text=True).strip()==PIN
    original=SRC.read_text()
    src=original
    marker="    return (\n"
    end="    )\n"
    assert src.count(marker)==1 and src.count(end)==1
    updated=src.replace(marker,"    _mg_equivalent_result_v6 = (\n",1).replace(
      end,end+"    return _mg_equivalent_result_v6\n",1)
    assert updated!=src
    assert updated.replace("    _mg_equivalent_result_v6 = (\n",marker,1).replace(
      end+"    return _mg_equivalent_result_v6\n",end,1)==src
    assert "s.replace(\"&\", \"&amp;\")" in updated
    mutated=updated.replace("s.replace(\"&\", \"&amp;\")",
                            "s.replace(\"&\", \"&\")",1)
    assert mutated!=updated
    try:
        baseline_native=direct_probe()
        baseline_tests=all_tests()
        SRC.write_text(updated)
        changed_native=direct_probe()
        changed_tests=all_tests()
        SRC.write_text(mutated)
        bad_native=direct_probe()
        bad_tests=all_tests()
        if not baseline_native["ok"] or not changed_native["ok"]:
            result_status="UNKNOWN_NATIVE_BEHAVIOR_NOT_QUALIFIED"
        elif not baseline_tests["ok"] or not changed_tests["ok"]:
            result_status="UNKNOWN_UPSTREAM_SUITE_FAILURE"
        elif bad_native["ok"]:
            result_status="REJECTED_NEGATIVE_MUTANT_UNDETECTED"
        else:
            result_status="PASS_POSTEXPOSURE_EXTERNAL_NATIVE_CALIBRATION"
        rows={"baseline_direct":baseline_native,"baseline_upstream_tests":baseline_tests,
             "changed_direct":changed_native,"changed_upstream_tests":changed_tests,
             "bad_mutant_direct":bad_native,"bad_mutant_upstream_tests":bad_tests}
        report={"status":result_status,"upstream":PIN,
            "original_source_sha256":hashlib.sha256(original.encode()).hexdigest(),
            "changed_source_sha256":hashlib.sha256(updated.encode()).hexdigest(),
            "source":"src/markupsafe/_native.py","postexposure_only":True,
            "original_sealed_v6":"UNKNOWN_NO_ELIGIBLE_REFRACTOR",
            "native_receipts":rows,
            "full_test_process_seconds":round(sum(x["seconds"] for x in rows.values()),6),
            "actual_skipped_tests":[],"source_depends_on_exposed_new_return_grammar":True,
            "semantic_scope":"controlled native strings only, not arbitrary locals/tracing/reflection",
            "equal_information_conventional":"SAME_NATIVE_TESTS_AND_MODULE_DEPENDENCY; TIE",
            "full_release":"UNKNOWN"}
        OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"status":result_status,
            "direct_probes":[baseline_native["ok"],changed_native["ok"],bad_native["ok"]],
            "upstream_suites":[baseline_tests["ok"],changed_tests["ok"],bad_tests["ok"]],
            "prior_v6":"UNKNOWN_NO_ELIGIBLE_REFRACTOR"},sort_keys=True))
        if result_status!="PASS_POSTEXPOSURE_EXTERNAL_NATIVE_CALIBRATION":
            raise RuntimeError("POSTEXPOSURE_NATIVE_QUALIFICATION_INCOMPLETE")
    finally:
        SRC.write_text(original)
if __name__=="__main__":main()
