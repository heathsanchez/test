#!/usr/bin/env python3
"""Post-run documentary, version-specific MathGraph warrant for Click V14 observations."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"mathgraph_pinned"))
from mathgraph_check.warrant_resolution import Claim,Receipt,Route,resolve_graph

RESULT=HERE/"result.json"
OUTPUT=HERE/"warrant.json"
EXPECTED_TEST_BLOB="7950a23ea3433fd0de98cac41fd81edf358d3f85"
EXPECTED_SOURCE_BLOB="b6e98a965a8fc136f9b1bc16ca7eb3616a21dc1c"
def require(condition,label):
    if not condition:raise AssertionError(label)

def run():
    raw=RESULT.read_bytes()
    result=json.loads(raw)
    require(result["status"]=="PASS_PROSPECTIVE_RUNTIME_EXCEPTION_AUTHORITY_ACQUISITION","UNQUALIFIED_NATIVE_SOURCE")
    require(result["test_git_blob"]==EXPECTED_TEST_BLOB,"TEST_BLOB_MISMATCH")
    require(result["source_git_blob"]==EXPECTED_SOURCE_BLOB,"SOURCE_BLOB_MISMATCH")
    require(result["source_identity_checked"],"SOURCE_AUTHORITY_UNQUALIFIED")
    require(result["original_native_suite_green"],"ORIGINAL_UPSTREAM_SUITE_FAILED")
    require(result["mutation_caused_native_suite_failure"],"MUTATION_NOT_CAUSAL")
    require(result["original_obligations_observed"]==5 and result["original_obligations_matched"]==5,"UNQUALIFIED_EXPECTATION_OBSERVATION")
    require(result["mutated_obligations_matched"]==0,"MUTATION_NOT_DETECTED")
    require(result["source_sha256_original"]!=result["source_sha256_mutated"],"SOURCE_VERSION_INCONSISTENT")
    original=result["original"]["runtime_obligation_receipt"]
    mutant=result["mutant"]["runtime_obligation_receipt"]
    require(original["test_source_sha256"]==mutant["test_source_sha256"],"TEST_IDENTITY_DRIFT")
    require(original["matched_occurrences"]==5 and mutant["matched_occurrences"]==0,"TRACE_CONTRADICTION")
    for record in original["obligations"]:
        require(record["native_context_accepted"] and
                record["expected_exception"]=="click.exceptions.BadParameter",
                "UNQUALIFIED_ERROR_TYPE")
    for record in mutant["obligations"]:
        require(not record["native_context_accepted"],"MUTANT_UNEXPECTED_ACCEPTANCE")

    source_scope="click:int_range:pytest-raises:V14:"+result["source_sha256_original"]
    claims=[Claim(name,"documentary",source_scope) for name in
         ("source_identity","test_identity","native_observation","mutation_control","protected_obligation","unrelated","full_application_release")]
    receipts=[Receipt(name,"documentary",source_scope) for name in
         ("source_hash","test_hash","native_trace","mutation_falsifier","policy","unrelated_receipt")]
    routes=[Route("source_identity",("source_hash",)),
        Route("test_identity",("test_hash",)),
        Route("native_observation",("native_trace",),("source_identity","test_identity")),
        Route("mutation_control",("mutation_falsifier",)),
        Route("protected_obligation",("policy",),("native_observation","mutation_control")),
        Route("unrelated",("unrelated_receipt",))]
    state=lambda withdrawn=frozenset():dict(resolve_graph(
        claims,routes,receipts,withdrawn=withdrawn).states)
    admitted=state()
    require(admitted["protected_obligation"]=="SOURCE_DOCUMENTED","SOURCE_OBLIGATION_UNWARRANTED")
    require(admitted["full_application_release"]=="UNKNOWN","RELEASE_WRONGLY_AUTHORIZED")
    require(admitted["unrelated"]=="SOURCE_DOCUMENTED","INDEPENDENT_LOST")
    withdrawn={}
    for receipt in ("source_hash","test_hash","native_trace","mutation_falsifier","policy"):
        after=state(frozenset({receipt}))
        require(after["protected_obligation"]=="UNKNOWN","FAILED_TO_RETRACT_"+receipt)
        require(after["unrelated"]=="SOURCE_DOCUMENTED","UNRELATED_CASCADE_"+receipt)
        withdrawn[receipt]="UNKNOWN"
    # The MUTATED source digest does not match frozen original-source authority.
    # Its native rejected requirement would also force the native_trace receipt
    # to be withheld regardless of source identity.
    mutated=state(frozenset({"source_hash","native_trace"}))
    require(mutated["protected_obligation"]=="UNKNOWN","MUTATED_SOURCE_UNSOUNDLY_ADMITTED")

    cross_boundary_rejected=False
    try:
        resolve_graph(
            [Claim("formal_obligation","formal",source_scope)],
            [Route("formal_obligation",("native_trace",))],receipts)
    except ValueError as e:
        cross_boundary_rejected="CROSS_BOUNDARY_EVIDENCE_WITHOUT_BRIDGE" in str(e)
    require(cross_boundary_rejected,"FORMAL_EVIDENCE_WRONGLY_ESCALATED")

    record={
      "status":"PASS_DOCUMENTARY_SOURCE_VERSION_RUNTIME_OBLIGATION_WARRANT",
      "native_evidence_sha256":hashlib.sha256(raw).hexdigest(),
      "source_scope":source_scope,
      "original_upstream_source_sha256":result["source_sha256_original"],
      "mutated_upstream_source_sha256":result["source_sha256_mutated"],
      "first_source_version_warrant":admitted["protected_obligation"],
      "source_modified_warrant":mutated["protected_obligation"],
      "selective_withdrawals":withdrawn,
      "independent_untouched":True,
      "forbidden_formal_promotion_rejected":cross_boundary_rejected,
      "full_application_release":admitted["full_application_release"],
      "documentary_only":True,
      "runtime_observation_vs_independent_replay":"RUNTIME_OBSERVATION_ONLY",
      "conventional_original_pytest":"SAME_NATIVE_MUTATION_FAILURE; NO ACCURACY_OR_COST_WIN",
      "R7_CLC":"UNCHANGED_NOT_REPLAYED"}
    OUTPUT.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":record["status"],"withdrawals":len(withdrawn),
       "original":record["first_source_version_warrant"],
       "mutated":record["source_modified_warrant"],
       "formal_promotion_rejected":cross_boundary_rejected,
       "full_release":record["full_application_release"]},sort_keys=True))
if __name__=="__main__":run()
