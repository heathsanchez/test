#!/usr/bin/env python3
"""Full-information strong-reviewer repair adequacy falsifier for ReviewBench #9.

The external strong-model golden already names the two pagination issues.
This audit uses the old source/native identity patch and tests newly supplied
from that GOLDEN. It is a retrospective verification/adequacy study, NOT
new discovery or a prospective matched-model comparison.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from replay_semantic import FROZEN_HEAD, SRC, TEST, NEW_FUNCTION

PAGINATION_TEST="internal/github/mgcheck_pagination_test.go"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def run(repo, *args):
    return subprocess.run(args,cwd=repo,capture_output=True,
                          text=True,timeout=240,check=False)

def read_test_outcome(text, expected):
    named="TestMGCheck"+expected
    # Fail closed if intended TEST FUNCTION never even ran.
    return named in text

def original_test_counts(text):
    return {
        "stale_wrong_sha_error": "stale-reviewed-different-sha-but-later-time" in text,
        "matching_sha_earlier_clock_error": "fresh-matching-sha-but-earlier-review-time" in text,
    }

def pagination_test_counts(text):
    return {
        "commit_page_2": "--- FAIL: TestMGCheckStrongReviewerPaginationResidual/commit_page_two_current_head" in text,
        "review_page_2": "--- FAIL: TestMGCheckStrongReviewerPaginationResidual/review_page_two_current_copilot" in text,
        "first_page_control": "--- PASS: TestMGCheckStrongReviewerSinglePageControl" in text,
        "native_test_executed": "=== RUN   TestMGCheckStrongReviewerPaginationResidual" in text,
    }

def test(repo, out, arm, pattern, label):
    command=("go","test","./internal/github","-run",pattern,"-count=1","-v")
    proc=run(repo,*command)
    log=(proc.stdout or "")+"\n"+(proc.stderr or "")
    name=arm+"-"+label+".log"
    (out/name).write_text(log)
    return {"arm":arm,"test":label,"command":" ".join(command),
            "exit_code":proc.returncode,"log_file":name,
            "log_sha256":digest(log.encode()),
            "identity_named_cases":original_test_counts(log),
            "pagination_named_cases":pagination_test_counts(log)}

def main():
    repo=Path(sys.argv[1]).resolve()
    out=Path(sys.argv[2]).resolve()
    out.mkdir(parents=True,exist_ok=True)
    actual=run(repo,"git","rev-parse","HEAD")
    if actual.returncode or actual.stdout.strip()!=FROZEN_HEAD:
        raise RuntimeError("UNKNOWN_SOURCE_IDENTITY: expected original exact ReviewBench PR head")
    original_path=repo/SRC
    identity_fixture=repo/TEST
    paging_fixture=repo/PAGINATION_TEST
    if identity_fixture.exists() or paging_fixture.exists():
        raise RuntimeError("UNKNOWN_COLLIDING_NATIVE_TEST_NAME")
    before=original_path.read_bytes()
    identity_data=(Path(__file__).parent/"semantic_review_identity_test.go").read_bytes()
    pagination_data=(Path(__file__).parent/"strong_reviewer_pagination_test.go").read_bytes()
    receipt={
        "original_github_sha":FROZEN_HEAD,
        "original_source_sha256":digest(before),
        "identity_fixture_sha256":digest(identity_data),
        "pagination_fixture_sha256":digest(pagination_data),
        "strong_comparator":"published ReviewBench golden, Claude Sonnet 4.6, already explicitly names both pagination TPs",
        "golden_git_blob":"4c49ff2fb925df6bcfecf30472e82f5b01fee4a0",
        "strong_model_inference_in_this_run":"NOT_RUN",
        "strong_model_cost":"UNKNOWN",
        "new_bug_discovery":"NO_KNOWN_TP_ONLY",
        "two_consequences":"commit-pagination after 30 and review-pagination after 30",
        "baseline_before_patch":"PUBLISHED_MODEL_ALREADY_DETECTED_TWO",
        "arms":[],
        "author_coded_native_tests":True,
        "patch_human_authored_before_this_experiment":True,
    }
    identity_fixture.write_bytes(identity_data)
    paging_fixture.write_bytes(pagination_data)
    try:
        for arm in ("original","identity_patch","restored_original"):
            if arm=="identity_patch":
                source=before.decode()
                begin=source.index("func (c *Client) IsCopilotReviewFresh(")
                end=source.index("func (c *Client) RequestCopilotReview(",begin)
                original_path.write_text(source[:begin]+NEW_FUNCTION+source[end:])
                receipt["candidate_patch_sha256"]=digest(original_path.read_bytes())
            elif arm=="restored_original":
                original_path.write_bytes(before)
                if digest(original_path.read_bytes())!=receipt["original_source_sha256"]:
                    raise RuntimeError("UNKNOWN_PATCH_REMOVAL_MISMATCH")
            identity=test(repo,out,arm,"^TestMGCheckCopilotHeadIdentityNotClock$","commit-identity")
            paging=test(repo,out,arm,
                        "^(TestMGCheckStrongReviewerPaginationResidual|TestMGCheckStrongReviewerSinglePageControl)$",
                        "pagination")
            receipt["arms"].append({"name":arm,"commit_identity":identity,"pagination":paging})

        original,patched,removed=receipt["arms"]
        identity_success=(
            original["commit_identity"]["exit_code"]!=0 and
            patched["commit_identity"]["exit_code"]==0 and
            removed["commit_identity"]["exit_code"]!=0 and
            all(original["commit_identity"]["identity_named_cases"].values()) and
            all(removed["commit_identity"]["identity_named_cases"].values()))
        paged=patched["pagination"]["pagination_named_cases"]
        original_paged=original["pagination"]["pagination_named_cases"]
        physically_open=(
            patched["pagination"]["exit_code"]!=0 and
            paged["commit_page_2"] and paged["review_page_2"] and
            paged["first_page_control"] and paged["native_test_executed"] and
            original_paged["commit_page_2"] and original_paged["review_page_2"])
        restoration=digest(original_path.read_bytes())==receipt["original_source_sha256"]
        receipt.update({
            "identity_regression_repaired_within_prior_four_cases":identity_success,
            "published_pagination_TPs_native_still_open":physically_open,
            "unresolved_pagination_count":2 if physically_open else None,
            "exact_original_source_recovered":restoration,
            "qualifier":(
                "WARRANTED_BOUNDED_PARTIAL_REPAIR_AND_PUBLISHED_STRONG_MODEL_RESIDUAL"
                if identity_success and physically_open and restoration else
                "UNKNOWN_OR_REJECTED_ADEQUACY_CHECK"),
            "product_safe_to_merge":"UNKNOWN",
            "reviewer_superiority_vs_strong_model":"NOT_WARRANTED",
            "practical_maintainer_action":"Do not treat four-case green patch as complete. Hold partial-closure claim; paginate commits and reviews, then requalify.",
            "published_baseline_detection_novelty":"REJECTED",
        })
    finally:
        original_path.write_bytes(before)
        identity_fixture.unlink(missing_ok=True)
        paging_fixture.unlink(missing_ok=True)
        receipt["final_original_exact"]=original_path.read_bytes()==before
        receipt["all_ephemeral_fixtures_removed"]=(
            not identity_fixture.exists() and not paging_fixture.exists())
        (out/"adequacy_report.json").write_text(
            json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "qualification":receipt["qualifier"],
        "old_identity_repaired":receipt["identity_regression_repaired_within_prior_four_cases"],
        "pagination_tps_still_open":receipt["published_pagination_TPs_native_still_open"],
        "strong_model_detected_them_first":True,
        "original_restored":receipt["final_original_exact"],
        "report_sha256":digest((out/"adequacy_report.json").read_bytes())
    },sort_keys=True))
    return 0 if receipt["qualifier"].startswith("WARRANTED") else 1

if __name__=="__main__":
    raise SystemExit(main())
