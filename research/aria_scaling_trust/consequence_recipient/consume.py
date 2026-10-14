#!/usr/bin/env python3
"""Independent, read-only recipient for source-pinned native consequence records.

Exact trusted policy Git-blob and original CI artifact SHA256 are inputs.
Neither a producer status string nor a passing CI summary grants authority.
No untrusted PR code is executed; all conclusions are historical and bounded.
"""
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

SCHEMA = "mathgraph.native-consequence-review-receipt.v1"
DIFF = "metalogic.cross-implementation-native-consequence.v1"
PROTECTED = "mathgraph.source-native-protected-go-test-conflict.v1"
SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA64 = re.compile(r"^[a-f0-9]{64}$")
NAME = re.compile(r"^[A-Za-z0-9_]+$")

class Refused(ValueError):
    pass

def insist(value, message):
    if not value:
        raise Refused(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def strict_json(raw):
    def pairs(items):
        result={}
        for k,v in items:
            insist(k not in result, "DUPLICATE_KEY")
            result[k]=v
        return result
    def deny_constant(_):
        raise Refused("NONFINITE_JSON")
    try:
        x=json.loads(raw.decode("utf-8"),object_pairs_hook=pairs,
                     parse_constant=deny_constant)
    except (ValueError,UnicodeError) as e:
        raise Refused("INVALID_JSON") from e
    insist(type(x) is dict,"INVALID_ROOT")
    return x

def policy_valid(raw,pin):
    insist(SHA40.fullmatch(pin) is not None and gitblob(raw)==pin,
           "EXTERNAL_POLICY_PIN_MISMATCH")
    p=strict_json(raw)
    insist(p.get("schema")=="mathgraph.evidence-policy.protected-consequence.v1"
           and p.get("owner")=="heathsanchez/test"
           and p.get("no_action_authorization") is True
           and p.get("warrant_scope")=="HISTORICAL_RESEARCH_ONLY",
           "UNAUTHORIZED_POLICY_SCOPE")
    insist(len(p.get("artifacts",[]))==2 and len(p.get("sources",[]))==3,
           "UNAUTHORIZED_POLICY_SET")
    for a in p["artifacts"]:
        insist(type(a["id"]) is int and a["id"]>0 and SHA64.fullmatch(a["sha256"])
               and type(a["name"]) is str,"INVALID_POLICY_ARCHIVE")
    for s in p["sources"]:
        insist(s.get("artifact") in {a["name"] for a in p["artifacts"]}
               and s.get("kind") in {"NATIVE_DIFFERENTIAL","NATIVE_GO_PROTECTED_TEST"}
               and SHA40.fullmatch(s["source_base"]) and
               SHA40.fullmatch(s["source_head"]) and
               re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",s["repository"]) and
               type(s["pr"]) is int and s["pr"]>0,
               "UNAUTHORIZED_POLICY_SUBJECT")
    insist(len({s["id"] for s in p["sources"]})==3,"DUPLICATE_POLICY_SUBJECT")
    return p

def archive(raw, pin):
    insist(len(raw)<=500000 and digest(raw)==pin,"ARCHIVE_DIGEST_NOT_AUTHORIZED")
    try:
        z=zipfile.ZipFile(io.BytesIO(raw))
        entries=z.infolist()
        insist(len(entries)<160 and len(entries)==len(set(e.filename for e in entries))
               and all(not e.is_dir() and e.file_size<400000 and
                       not e.filename.startswith("/") and
                       ".." not in Path(e.filename).parts for e in entries)
               and sum(e.file_size for e in entries)<1800000,
               "UNSAFE_ARCHIVE")
        return z
    except (OSError,zipfile.BadZipFile):
        raise Refused("INVALID_ARCHIVE") from None

def comparable(x):
    if type(x) is dict:
        return {k:comparable(v) for k,v in x.items() if k!="seconds"}
    if type(x) is list:
        return [comparable(v) for v in x]
    return x

def diff_obs(record,src):
    insist(record.get("schema")==DIFF
           and record.get("result")=="WARRANTED_BOUNDED_NATIVE_DIFFERENTIAL_REPAIRED"
           and record.get("method_autonomously_invented")=="NO"
           and record.get("generator")=="HUMAN_WRITTEN_DECLARATIVE_DOMAIN_EXHAUSTION"
           and record.get("ablation") is None and record.get("withdrawal") is False
           and record.get("action_authorization")=="NONE",
           "DIFFERENTIAL_SCOPE_NOT_WARRANTED")
    sources={s["name"]:s["sha"] for s in record["sources"]}
    insist(sources=={"original_base":src["source_base"],
                     "original_head":src["source_head"]},"SOURCE_SHA_CHANGED")
    obs=record.get("observations")
    insist(type(obs) is list and len(obs)==record.get("domain_size")
           and 0<len(obs)<=5000,"DOMAIN_MISMATCH")
    counts=collections.Counter()
    mismatches=[]
    controls=[]
    for case in obs:
        arms=case.get("arms")
        insist(type(arms) is dict and
               set(arms)=={"reference","base","head"},"WRONG_EXECUTION_ARMS")
        a,b,c=[arms[k] for k in ("reference","base","head")]
        statuses=[v.get("status") for v in (a,b,c)]
        if statuses==["VALUE","VALUE","VALUE"]:
            insist(all("value" in v for v in (a,b,c)),
                   "VALUE_WITHOUT_OUTPUT")
            lhs="EQUAL" if comparable(a["value"])==comparable(b["value"]) else "DIFFERENT"
            rhs="EQUAL" if comparable(a["value"])==comparable(c["value"]) else "DIFFERENT"
            insist(case["base_reference"]==lhs and case["head_reference"]==rhs,
                   "FORGED_DIFFERENTIAL_CLASSIFICATION")
            if lhs=="DIFFERENT":
                counts["base_reference_value_mismatches"]+=1
                if rhs=="EQUAL":
                    counts["mismatches_repaired_at_head"]+=1
                    mismatches.append(case)
                else: counts["unrepaired_base_differences"]+=1
            elif rhs=="EQUAL":
                counts["both_equal_controls"]+=1
                controls.append(case)
            else: counts["new_head_regressions"]+=1
        else:
            insist("UNKNOWN" in (case.get("base_reference"),
                                 case.get("head_reference")),
                   "INCOMPLETE_EXECUTION_MISSTATED")
            counts["timeouts_or_incomplete_evidence"]+=1
    claimed=record.get("counts")
    insist(type(claimed) is dict and
           set(claimed)==set(["base_reference_value_mismatches",
           "mismatches_repaired_at_head","unrepaired_base_differences",
           "new_head_regressions","both_equal_controls",
           "timeouts_or_incomplete_evidence"]) and
           all(type(v) is int and counts[k]==v for k,v in claimed.items()),
           "COUNTS_NOT_RECOMPUTED")
    insist(mismatches and controls and
           counts["new_head_regressions"]==0 and
           counts["unrepaired_base_differences"]==0,
           "NO_REPAIRED_NATIVE_DISAGREEMENT")
    def matches(case,expected):
        return comparable({**case["arms"],"input":case["input"]})==comparable(expected)
    chosen=record.get("minimal_witness")
    ctrl=record.get("negative_control")
    insist(type(chosen) is dict and type(ctrl) is dict and
           any(matches(c,chosen) for c in mismatches) and
           any(matches(c,ctrl) for c in controls),
           "WITNESS_OR_NEGATIVE_NOT_IN_NATIVE_CASES")
    baseline=record.get("fully_informed_baseline") or {}
    insist(baseline.get("can_reproduce_same_witness")=="YES" and
           baseline.get("reviewer_decision_superiority")=="NOT_PROVEN",
           "STRONG_BASELINE_NOT_RETAINED")
    return {"kind":"EXECUTABLE_IMPLEMENTATION_DISAGREEMENT",
            "status":"WARRANTED_BOUNDED_HISTORICAL_NATIVE_OBSERVATION",
            "domain_size":len(obs),
            "base_mismatch_count":counts["base_reference_value_mismatches"],
            "fixed_head_mismatch_count":counts["mismatches_repaired_at_head"],
            "unknown_cases":counts["timeouts_or_incomplete_evidence"],
            "witness":comparable(chosen),
            "agreeing_control":comparable(ctrl),
            "next_action":"Inspect original native disagreement against the chosen reference semantics; preserve untested cases as UNKNOWN.",
            "operation_generator_human_written":True}

def diff_controls(z,record,names):
    for filename in names:
        ctrl=strict_json(z.read(filename))
        insist(ctrl.get("schema")==DIFF and
               ctrl.get("family")==record.get("family") and
               ctrl.get("sources")==record.get("sources"),
               "NEGATIVE_CONTROL_IDENTITY_CHANGED")
        cases=ctrl.get("observations")
        insist(type(cases) is list and
               len(cases)==len(record["observations"]),
               "NEGATIVE_CONTROL_DOMAIN_CHANGED")
        if ctrl.get("ablation")=="reference":
            insist(ctrl.get("result")=="UNKNOWN_REQUIRED_BACKEND_REMOVED" and
                   ctrl.get("minimal_witness") is None and
                   all(v["arms"]["reference"]["status"]=="ABLATION_UNAVAILABLE"
                       and v["base_reference"]=="UNKNOWN" and
                       v["head_reference"]=="UNKNOWN" for v in cases),
                   "REFERENCE_REMOVAL_WOULD_FALSELY_PROMOTE")
        elif ctrl.get("withdrawal") is True:
            insist(ctrl.get("result")=="STALE_EVIDENCE_WITHDRAWN" and
                   all(comparable(a["input"])==comparable(b["input"]) and
                       comparable(a["arms"])==comparable(b["arms"])
                       for a,b in zip(record["observations"],cases)),
                   "WITHDRAWAL_ERASED_HISTORY_OR_STILL_WARRANTED")
        else: raise Refused("UNKNOWN_NEGATIVE_CONTROL")
    return len(names)

def test_body(source,test):
    insist(re.fullmatch(r"Test[A-Za-z0-9_]+",test),"UNSAFE_TEST_NAME")
    lines=source.decode().splitlines(keepends=True)
    start=next((i for i,v in enumerate(lines) if re.match(
        r"^func\s+"+re.escape(test)+r"\s*\(\s*t\s+\*testing.T\s*\)",v)),None)
    insist(start is not None,"OLD_TEST_SOURCE_NOT_FOUND")
    end=next((i for i in range(start+1,len(lines)) if re.match(
        r"^func\s+[A-Za-z_]",lines[i])),len(lines))
    return "".join(lines[start:end]).encode()

def get_source(item,policy,revision):
    path=item["original_source"]
    insist(type(path) is str and path.endswith("_test.go") and
           ".." not in Path(path).parts and not path.startswith("/"),
           "UNSAFE_SOURCE_FILE")
    url=("https://raw.githubusercontent.com/"+policy["repository"]+"/"+
         policy[revision]+"/"+path)
    with urllib.request.urlopen(
        urllib.request.Request(url,headers={"User-Agent":"MathGraphReadOnlyAudit"}),
        timeout=30
    ) as r:
        b=r.read(400001)
    insist(len(b)<400001,"UPSTREAM_SOURCE_TOO_LARGE")
    return b

def protected_obs(record,z,src,source_reader=get_source):
    insist(record.get("schema")==PROTECTED and
           record.get("status")=="WARRANTED_BOUNDED_ORIGINAL_TEST_CONTRACT_CONFLICT"
           and record.get("error") is None and
           record.get("source")=={"repository":src["repository"],
              "original_base":src["source_base"],
              "contributor_head":src["source_head"]},
           "PROTECTED_SOURCE_SCOPE_NOT_WARRANTED")
    steps=record.get("steps")
    insist(type(steps) is list and 25<=len(steps)<=70,
           "PROTECTED_LOG_SET_INCOMPLETE")
    logs={}
    for e in steps:
        key=e["name"]
        insist(type(key) is str and NAME.fullmatch(key)
               and key not in logs and SHA64.fullmatch(e["sha256"])
               and type(e["exit_code"]) is int and
               e["exit_code"] in e["valid_codes"],
               "INVALID_NATIVE_LOG")
        data=z.read(key+".log")
        insist(digest(data)==e["sha256"] and
               data.startswith(("$ "+" ".join(e["argv"])+"\n").encode()),
               "NATIVE_COMMAND_LOG_INTEGRITY_FAIL")
        logs[key]={"metadata":e,"text":data.decode()}
    names=record.get("unchanged_old_tests_failing_at_contributor_head")
    packages=record.get("native_package_results")
    insist(type(names) is dict and bool(names) and type(packages) is dict,
           "NO_PROTECTED_CONFLICT")
    found=[]
    for package,entries in names.items():
        state=packages.get(package)
        insist(state and all(state.get(k)==v for k,v in {
            "original_base_suite_exit":0,
            "head_touched_tests_exit":0,"head_full_suite_exit":1,
            "head_with_only_conflicting_old_test_ablated_exit":0,
            "head_reinstated_old_test_exit":1,
            "ablation_recovered_exit":0}.items()),"CAUSAL_GATE_FAIL")
        prefix=next((key[:-len("_head_all")] for key,v in logs.items()
                     if key.endswith("_head_all") and
                     v["metadata"]["argv"][-1]==package),None)
        insist(prefix is not None and
               logs[prefix+"_head_all"]["metadata"]["exit_code"]==1 and
               logs[prefix+"_head_touched"]["metadata"]["exit_code"]==0 and
               logs[prefix+"_original_base_all"]["metadata"]["exit_code"]==0 and
               logs[prefix+"_base_original_plus_head_tests"]["metadata"]["exit_code"]==1 and
               logs[prefix+"_old_restored_after_ablation"]["metadata"]["exit_code"]==0,
               "NATIVE_EXECUTION_CAUSAL_GATE_FAIL")
        ablated=next((x for k,x in logs.items()
                      if k.endswith("_head_only_old_failing_test_ablated")),None)
        restored=next((x for k,x in logs.items()
                       if k.endswith("_head_original_failing_test_restored")),None)
        insist(ablated and restored and
               ablated["metadata"]["exit_code"]==0 and
               restored["metadata"]["exit_code"]==1 and
               "PROTECTED_TEST_ABLATED" in ablated["text"],
               "OLD_TEST_ABLATION_LOG_MISSING")
        for entry in entries:
            test=entry["test"]
            insist(test in state["head_full_failed_tests"] and
                   test in state["head_ablation_scope"] and
                   entry.get("original_test_body_unchanged") is True and
                   re.search(r"(?m)^\s*--- FAIL: "+re.escape(test)+r"\b",
                             logs[prefix+"_head_all"]["text"]) and
                   test in restored["text"],"PROTECTED_FAILURE_NOT_OBSERVED")
            a=source_reader(entry,src,"source_base")
            b=source_reader(entry,src,"source_head")
            insist(gitblob(a)==src["source_go_file_blob_original"] and
                   gitblob(b)==src["source_go_file_blob_head"],
                   "ORIGINAL_UPSTREAM_TEST_FILE_PIN_FAIL")
            text_a=test_body(a,test)
            text_b=test_body(b,test)
            insist(text_a==text_b and
                   digest(text_a)==entry["exact_test_body_sha256"],
                   "UNCHANGED_ORIGINAL_TEST_IDENTITY_FAIL")
            found.append({"package":package,"test":test,
                          "file":entry["original_source"],
                          "test_sha256":entry["exact_test_body_sha256"]})
    return {"kind":"PROTECTED_OLD_TEST_CONTRADICTION",
            "status":"WARRANTED_BOUNDED_HISTORICAL_NATIVE_OBSERVATION",
            "native_logs_replayed":len(logs),
            "unchanged_tests":found,
            "causal_controls":"OLD_BASE_GREEN_HEAD_TOUCHED_GREEN_HEAD_FULL_RED_SINGLE_OLD_TEST_ABLATION_GREEN_RESTORE_RED",
            "next_action":"Reconcile the protected older test with the contributor's newly accepted behavior; changed tests alone do not settle the contract.",
            "operation_generator_human_written":True}

def reconcile(policy_raw,pin,archives,source_reader=get_source):
    p=policy_valid(policy_raw,pin)
    by_archive={a["name"]:a for a in p["artifacts"]}
    insist(set(archives)==set(by_archive),"REQUIRED_ARCHIVES_MISSING")
    zips={name:archive(archives[name],spec["sha256"])
          for name,spec in by_archive.items()}
    items=[]
    for s in p["sources"]:
        z=zips[s["artifact"]]
        r=strict_json(z.read(s["member"]))
        if s["kind"]=="NATIVE_DIFFERENTIAL":
            item=diff_obs(r,s)
            item["negative_controls_checked"]=diff_controls(
                z,r,s.get("negative_controls",[]))
        else:
            item=protected_obs(r,z,s,source_reader=source_reader)
        items.append({
            "subject":{"repository":s["repository"],"pr":s["pr"],
                       "base_sha":s["source_base"],"head_sha":s["source_head"]},
            "archive":{"artifact_id":by_archive[s["artifact"]]["id"],
                       "sha256":by_archive[s["artifact"]]["sha256"],
                       "member":s["member"]},
            **item,
            "current_upstream":"NOT_CHECKED",
            "live_publisher_withdrawal":"NOT_CHECKED",
            "full_semantic_fidelity":"NOT_ESTABLISHED",
            "action_authority":"NONE"
        })
    return {"schema":SCHEMA,"policy_git_blob":pin,"status":"WARRANTED_BOUNDED_HISTORICAL_CONSEQUENCE_RECONCILIATION",
            "receipts":items,"live_check_published":False,
            "reviewer_baseline":"FULL_INFORMATION_CONVENTIONAL_CAN_FIND_SAME",
            "measured_review_cost_advantage":"NOT_MEASURED",
            "generator_self_invention":"NOT_ESTABLISHED",
            "action_authority":"NONE"}

def render(result):
    lines=["# MathGraph Check — read-only native consequence preview","",
           "No GitHub Check or PR comment posted. Evidence is historical and exact-source-scoped.",""]
    for x in result["receipts"]:
        s=x["subject"]
        lines+=["## "+s["repository"]+" PR #"+str(s["pr"]),
                "Evidence kind: "+x["kind"],"Base: "+s["base_sha"],
                "Contributor head: "+s["head_sha"],
                "Archive SHA256: "+x["archive"]["sha256"],""]
        if "witness" in x:
            w=x["witness"]
            lines+=["Input: "+json.dumps(w["input"],sort_keys=True),
                    "Reference: "+json.dumps(w["reference"]["value"]),
                    "Original: "+json.dumps(w["base"]["value"]),
                    "Contributor head: "+json.dumps(w["head"]["value"]),
                    "Incomplete observed cases: "+str(x["unknown_cases"])]
        else:
            lines+=["Protected unchanged test: "+n["test"]+" in "+n["file"]
                    for n in x["unchanged_tests"]]
        lines+=["Next action: "+x["next_action"],"",
                "No assertion of an unfixed current defect or independent reviewer advantage.",""]
    lines+=["Authority: ADVISORY_ONLY. No source writes, merges, external deployments or L7 claims.",
            "Fully informed conventional review can reach the same verdicts.",
            "Measured reviewer benefit: NOT_MEASURED.",""]
    return "\n".join(lines)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--policy",type=Path,required=True)
    a.add_argument("--external-git-blob",required=True)
    a.add_argument("--archives",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    opts=a.parse_args()
    try:
        policy_raw=opts.policy.read_bytes()
        p=policy_valid(policy_raw,opts.external_git_blob)
        contents={item["name"]:(opts.archives/(item["name"]+".zip")).read_bytes()
                  for item in p["artifacts"]}
        response=reconcile(policy_raw,opts.external_git_blob,contents)
    except (Refused,OSError,ValueError,KeyError,zipfile.BadZipFile) as err:
        print(json.dumps({"accepted":False,"reason":str(err)}),file=sys.stderr)
        return 1
    opts.out.mkdir(parents=True,exist_ok=True)
    (opts.out/"review.json").write_text(json.dumps(response,sort_keys=True,indent=2)+"\n")
    (opts.out/"review.md").write_text(render(response))
    print(json.dumps({"status":response["status"],
          "kinds":[x["kind"] for x in response["receipts"]],
          "receipts":len(response["receipts"]),"live_check_published":False}))
    return 0

if __name__=="__main__":
    sys.exit(main())
