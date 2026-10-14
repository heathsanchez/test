#!/usr/bin/env python3
"""Known strong-reviewer findings -> bounded native verification and repair.

This is a fully-informed historical Go repair. New patch code is human-authored
from already-published public Claude findings and the PR's own contract.
It is NOT autonomous method genesis or a live strong-model head-to-head.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from replay_semantic import FROZEN_HEAD, SRC, TEST, NEW_FUNCTION

PAGING = "internal/github/mgcheck_pagination_test.go"

def sha(x):
    return hashlib.sha256(x).hexdigest()

def run(repo, *args):
    return subprocess.run(args,cwd=repo,text=True,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,timeout=240,check=False)

def check(repo,out,arm,tag,pattern):
    cmd=("go","test","./internal/github","-run",pattern,"-count=1","-v")
    p=run(repo,*cmd)
    logfile=arm+"_"+tag+".log"
    (out/logfile).write_text(p.stdout)
    return {"name":tag,"exit_code":p.returncode,
            "log_file":logfile,"log_sha256":sha(p.stdout.encode()),
            "output_tail":p.stdout[-1700:]}

def function_replace(original, function):
    text=original.decode()
    first=text.index("func (c *Client) IsCopilotReviewFresh(")
    last=text.index("func (c *Client) RequestCopilotReview(",first)
    repaired=text[:first]+function+text[last:]
    # Original source only used "time" for the method being rewritten.
    return repaired.replace('\t"time"\n',"").encode()

def main():
    repo=Path(sys.argv[1]).resolve()
    out=Path(sys.argv[2]).resolve()
    out.mkdir(parents=True,exist_ok=True)
    g=run(repo,"git","rev-parse","HEAD")
    if g.returncode or g.stdout.strip()!=FROZEN_HEAD:
        raise RuntimeError("UNKNOWN_ORIGINAL_SUBJECT_SHA")
    path=repo/SRC
    fixture=repo/TEST
    paging_fixture=repo/PAGING
    if fixture.exists() or paging_fixture.exists():
        raise RuntimeError("UNKNOWN_EXISTING_TEST_FIXTURE_CONFLICT")
    original=path.read_bytes()
    old_function=NEW_FUNCTION
    new_function=(Path(__file__).parent/"strong_reviewer_resolution_function.go.txt").read_text()
    first_patch=function_replace(original,old_function)
    revised_patch=function_replace(original,new_function)
    original_fixture=(Path(__file__).parent/"semantic_review_identity_test.go").read_bytes()
    second_fixture=(Path(__file__).parent/"strong_reviewer_pagination_test.go").read_bytes()
    identity_pattern="^TestMGCheckCopilotHeadIdentityNotClock$"
    paging_pattern="^(TestMGCheckStrongReviewerPaginationResidual|TestMGCheckStrongReviewerSinglePageControl)$"
    negative_pattern="^(TestMGCheckStrongReviewerDismissedNotFresh|TestMGCheckStrongReviewerMissingHeadFailsClosed)$"
    report={
        "original_reviewbench_sha":FROZEN_HEAD,
        "source_file":SRC,
        "original_source_sha256":sha(original),
        "prior_partial_patch_sha256":sha(first_patch),
        "improved_candidate_sha256":sha(revised_patch),
        "native_fixture_identity_sha256":sha(original_fixture),
        "native_fixture_pagination_sha256":sha(second_fixture),
        "published_baseline":"ReviewBench golden strong Claude Sonnet 4.6 already reports identity and both pagination defects",
        "model_inference":"NOT_RUN",
        "patch_authorship":"human-authored from known published review, NOT agent invention",
        "arms":[],
        "full_repo_suite":"NOT_RUN",
        "product_merge_authority":"UNKNOWN",
        "reviewer_superiority":"NOT_ESTABLISHED",
        "source_variants_ephemeral":True,
    }
    fixture.write_bytes(original_fixture)
    paging_fixture.write_bytes(second_fixture)
    try:
        for arm,content in (("original",original),
                            ("previous_identity_patch",first_patch),
                            ("reviewer_informed_candidate",revised_patch),
                            ("physically_restored_original",original)):
            path.write_bytes(content)
            parts=[
                check(repo,out,arm,"identity",identity_pattern),
                check(repo,out,arm,"pagination",paging_pattern),
                check(repo,out,arm,"negative_controls",negative_pattern)]
            report["arms"].append({"name":arm,"source_sha256":sha(content),"tests":parts})
        old,partial,revised,restored=report["arms"]
        # Native partiality: earlier four-case patch solves exactly its
        # announced boundary, while original model-found paging cases remain.
        partiality=(
            old["tests"][0]["exit_code"]!=0 and
            partial["tests"][0]["exit_code"]==0 and
            partial["tests"][1]["exit_code"]!=0)
        pagination_ok=revised["tests"][1]["exit_code"]==0
        identity_ok=revised["tests"][0]["exit_code"]==0
        negatives_ok=revised["tests"][2]["exit_code"]==0
        source_ablated=(restored["tests"][0]["exit_code"]!=0 and
                        restored["tests"][1]["exit_code"]!=0 and
                        sha(path.read_bytes())==sha(original))
        # Verify that success was NOT just a zero-tests invocation.
        concat_logs="\n".join((out/t["log_file"]).read_text() for t in revised["tests"])
        name_check=all(x in concat_logs for x in (
            "TestMGCheckCopilotHeadIdentityNotClock",
            "TestMGCheckStrongReviewerPaginationResidual/commit_page_two_current_head",
            "TestMGCheckStrongReviewerPaginationResidual/review_page_two_current_copilot",
            "TestMGCheckStrongReviewerSinglePageControl",
            "TestMGCheckStrongReviewerDismissedNotFresh",
            "TestMGCheckStrongReviewerMissingHeadFailsClosed"))
        # Run original native package tests ON the patched source; earlier
        # experiments only proved the local four-case fixture.
        path.write_bytes(revised_patch)
        package_test=run(repo,"go","test","./internal/github","-count=1")
        (out/"candidate-original-package.log").write_text(package_test.stdout)
        report["original_native_package_test"]={
            "exit_code":package_test.returncode,
            "log_sha256":sha(package_test.stdout.encode()),
            "output_tail":package_test.stdout[-1500:]}
        report["scoped_controls"]={
            "previous_patch_inadequate_on_published_TPs":partiality,
            "improved_candidate_identity_suite_passes":identity_ok,
            "improved_candidate_pagination_suite_passes":pagination_ok,
            "dismissed_and_missing_source_controls_pass":negatives_ok,
            "physical_patch_removal_restores_native_failure":source_ablated,
            "all_six_required_native_test_names_executed":name_check,
            "original_native_package_suite_passed":package_test.returncode==0,
        }
        passed=all(report["scoped_controls"].values())
        report["qualification"]=(
            "WARRANTED_BOUNDED_KNOWN_STRONG_MODEL_ISSUES_REPAIRED_AND_CAUSALLY_TESTED"
            if passed else "UNKNOWN_OR_REJECTED_STRONG_REVIEWER_INFORMED_REPAIR")
        report["remaining_unknown"]=[
            "all downstream consumers and external user subclasses",
            "general Github pagination past 100 pages",
            "shared API call minimization and broad application flow",
            "genuinely unseen bug discovery beyond public strong reviewer",
            "cost and time advantage over actual equally equipped strong coding agents"]
        report["product_reviewer_action"]=(
            "Bounded source-native repair candidate ready for human review; "
            "do not call original PR universally safe or merged")
    finally:
        path.write_bytes(original)
        fixture.unlink(missing_ok=True)
        paging_fixture.unlink(missing_ok=True)
        report["final_original_source_restored"]=path.read_bytes()==original
        report["final_test_files_removed"]=not fixture.exists() and not paging_fixture.exists()
        (out/"strong_resolution_report.json").write_text(
            json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "qualification":report["qualification"],
        "scoped_controls":report["scoped_controls"],
        "final_original_source_restored":report["final_original_source_restored"],
        "report_sha256":sha((out/"strong_resolution_report.json").read_bytes()),
        "strong_model_novelty":"NONE - known model issues"
    },sort_keys=True))
    return 0 if report["qualification"].startswith("WARRANTED") else 1

if __name__=="__main__":
    raise SystemExit(main())
