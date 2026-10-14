#!/usr/bin/env python3
"""Read-only strong-reviewer finding → source-native evidence and repair receipt.

The test and candidate fix are human-authored retrospective adapters. Existing
reviewer finding is a proposal, not an independent executable proof.
Only owned CI ephemeral source worktrees are modified.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HEAD="e1477f8b3f18c1de6ff87dbca9465a7b106dc193"
SRC="src/gimmes/strategy/staleness.py"
FIXTURE="tests/unit/test_mgcheck_review_uplift.py"
ORIGINAL="volume = m.volume_24h if m.volume_24h > 0 else m.volume"
PATCHED="volume = m.volume_24h"


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def invoke(repo, *args, timeout=180):
    start=time.monotonic()
    env=dict(os.environ)
    env["PYTHONPATH"]=str(repo/"src")
    p=subprocess.run(args,cwd=repo,env=env,text=True,capture_output=True,
                     timeout=timeout,check=False)
    return {"exit":p.returncode,"duration_seconds":round(time.monotonic()-start,4),
            "log":(p.stdout or "")+(p.stderr or "")}


def save(out,name,entry):
    log=entry.pop("log")
    (out/(name+".log")).write_text(log)
    entry["log_sha256"]=sha(log.encode())
    entry["log_last_lines"]=log.splitlines()[-18:]
    return entry


def run(repo,out):
    out.mkdir(parents=True,exist_ok=True)
    report={"subject_head":HEAD,"observer":"human_authored_after_public_strong_finding",
            "strong_reviewer":"ReviewBench llm_review:claude-sonnet-4.6 / gimmes#468",
            "review_input_status":"PUBLIC_PRIOR_FINDING_NOT_RERUN",
            "same_information_live_agent":"NOT_RUN",
            "no_upstream_mutations":True,"scope":"one market staleness policy and targeted unit suite"}
    git=invoke(repo,"git","rev-parse","HEAD")
    if git["exit"] or git["log"].strip()!=HEAD:
        raise RuntimeError("UNKNOWN_SOURCE_IDENTITY")
    path=repo/SRC
    fixture=repo/FIXTURE
    orig=path.read_bytes()
    if fixture.exists():
        raise RuntimeError("FIXTURE_ALREADY_EXISTS")
    if orig.decode().count(ORIGINAL)!=1:
        raise RuntimeError("UNKNOWN_UNIQUE_REPAIR_SITE")
    fixture_bytes=(Path(__file__).parent/"test_gimmes_review.py").read_bytes()
    report["original_source_sha256"]=sha(orig)
    report["observer_sha256"]=sha(fixture_bytes)
    completed=False
    try:
        fixture.write_bytes(fixture_bytes)
        orig_unaltered=save(out,"original_unit_suite",invoke(repo,sys.executable,"-m","pytest","-q","tests/unit/test_staleness.py"))
        report["old_targeted_suite"]=orig_unaltered
        orig_test=save(out,"original_review_witness",invoke(repo,sys.executable,"-m","pytest","-q",FIXTURE))
        report["original_native_observer"]=orig_test
        # Expected original defect: one failed scoped test, six protected successes.
        if orig_unaltered["exit"] or orig_test["exit"]==0:
            raise RuntimeError("UNKNOWN_EXPECTED_OLD_BEHAVIOR")
        if not any("1 failed, 6 passed" in s or "6 passed, 1 failed" in s for s in orig_test["log_last_lines"]):
            raise RuntimeError("UNKNOWN_FAILURE_NOT_TARGETED")
        patch=orig.decode().replace(ORIGINAL,PATCHED,1).encode()
        path.write_bytes(patch)
        report["candidate_source_sha256"]=sha(patch)
        patched_suite=save(out,"candidate_review_and_suite",invoke(repo,sys.executable,"-m","pytest","-q","tests/unit/test_staleness.py",FIXTURE))
        report["candidate_native_observer_and_old_suite"]=patched_suite
        if patched_suite["exit"]:
            raise RuntimeError("CANDIDATE_PATCH_REJECTED")
        # Separate negative: merely preferring history cannot solve this observer.
        path.write_bytes(orig.decode().replace(ORIGINAL,"volume = m.volume",1).encode())
        bad=save(out,"wrong_candidate_negative",invoke(repo,sys.executable,"-m","pytest","-q",FIXTURE))
        report["deliberately_wrong_candidate"]=bad
        if bad["exit"]==0:
            raise RuntimeError("NEGATIVE_FALSE_ACCEPT")
        path.write_bytes(orig)
        restored=save(out,"physically_restored_observer",invoke(repo,sys.executable,"-m","pytest","-q",FIXTURE))
        report["physical_patch_removal"]=restored
        if restored["exit"]==0:
            raise RuntimeError("ABLATON_DID_NOT_REPRODUCE")
        if not any("1 failed, 6 passed" in s or "6 passed, 1 failed" in s for s in restored["log_last_lines"]):
            raise RuntimeError("RESTORE_FAILED_FOR_WRONG_REASON")
        completed=True
        report["qualification"]="WARRANTED_BOUNDED_KNOWN_REVIEW_FINDING_NATIVE_REMEDIATION"
    finally:
        path.write_bytes(orig)
        if fixture.exists(): fixture.unlink()
        report["final_exact_original_source_restored"]=sha(path.read_bytes())==sha(orig)
        report["temporary_test_removed"]=not fixture.exists()
        report["native_execution_completed"]=completed
        (out/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if not report["final_exact_original_source_restored"] or not report["temporary_test_removed"]:
        raise RuntimeError("FAILED_RESTORATION")
    if not completed:
        raise RuntimeError("INCOMPLETE_EVIDENCE")
    return report


if __name__=="__main__":
    try:
        report=run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
        print(json.dumps({k:v for k,v in report.items()
          if k in ("subject_head","qualification","original_source_sha256",
                   "candidate_source_sha256","final_exact_original_source_restored",
                   "temporary_test_removed","observer_sha256","review_input_status")},sort_keys=True))
    except Exception as e:
        print("SOURCE_NATIVE_EVIDENCE_GATE_FAILED:"+repr(e),file=sys.stderr)
        sys.exit(2)
