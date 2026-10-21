#!/usr/bin/env python3
"""POST-RUN V9b: pre-header-test skip prediction and independent later audit."""
import importlib.util,json,statistics,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("v9_frozen_source",HERE/"experiment.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=HERE/"predecision_audit.json"

def main():
    original,headers=m.pin()
    decisions=[]
    try:
        for name,value in m.EDIT.items():
            candidate=original.replace(m.OLD,value,1)
            m.SOURCE.write_text(candidate)
            # PROPOSAL generated here, before the candidate header suite is run.
            shape=m.structural_admission(original,candidate,headers,headers,name)
            owner=m.run_suite(m.OWNER,name+":predecision_owner")
            proposed_skip=shape["admitted"] and owner["ok"]
            # Only now independently audit the omitted candidate test.
            header=m.run_suite(m.HEADERS,name+":later_header_audit")
            checked=(header["ok"] and header["trace"].get("target_calls")==0)
            decisions.append({"variant":name,"pre_header_test_proposed_skip":proposed_skip,
                "owner_passed":owner["ok"],"header_audit_passed":header["ok"],
                "header_audit_zero_calls":checked,
                "proposed_skip_confirmed":proposed_skip and checked,
                "owner_seconds":owner["elapsed_seconds"],
                "audit_seconds":header["elapsed_seconds"],
                "conventional_cached_coverage_proposal":proposed_skip})
    finally:
        m.SOURCE.write_text(original)
        m.HEADERS.write_text(headers)
    assert [x["pre_header_test_proposed_skip"] for x in decisions]==[True,True,True,False]
    assert all(x["proposed_skip_confirmed"] for x in decisions[:3])
    assert not decisions[3]["proposed_skip_confirmed"]
    # Actual qualified work includes every test: historical reuse is
    # potential, not a measured reduction in this experiment's full cost.
    report={"status":"PASS_POSTRUN_PREHEADER_TEST_PREDICTION",
       "underlying_first_run":"https://github.com/heathsanchez/test/actions/runs/39692932503",
       "candidate":decisions,
       "predictions_before_new_header_tests":3,
       "falsified_negative_before_header_test":1,
       "conventional_cached_coverage":"TIE_SAME_THREE_PRETEST_PREDICTIONS",
       "hypothetical_avoided_header_test_seconds":round(sum(x["audit_seconds"] for x in decisions[:3]),6),
       "actual_qualification_test_process_seconds":round(sum(x["owner_seconds"]+x["audit_seconds"] for x in decisions),6),
       "full_application_release":"UNKNOWN",
       "qualification_limits":["POSTEXPOSURE protocol after sealed V9 first outcomes",
         "static source-edit envelope is not a Python semantic noninterference theorem",
         "future different test/runtime/source invalidates historical zero-call premise",
         "all candidate header tests WERE RUN in independent audit",
         "conventional source-aware cached-coverage model offers same decision"]
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],
         "proposed":[x["pre_header_test_proposed_skip"] for x in decisions],
         "post_audit":[x["proposed_skip_confirmed"] for x in decisions],
         "hypothetical_header_seconds":report["hypothetical_avoided_header_test_seconds"],
         "conventional":"TIE"},sort_keys=True))
if __name__=="__main__":main()
