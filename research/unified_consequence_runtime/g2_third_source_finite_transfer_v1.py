#!/usr/bin/env python3
"""Prospective unchanged Mistral/Deer finite source-mask method on NEW native source.

The original source pool, exact byte-locked operation family, first actual native
failure rule, informed executable ledger, and costs were frozen before ANY new
source or author test body access at prequery e40ff465. Third-source transfer,
not arbitrary meta-language invention. A selected inapplicable method is a
legitimate negative. NO untrusted code is claimed sandboxed.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from . import g2_pool_first_native_failure_v1 as native_pool
from . import g2_finite_composition_mistral_v2 as learned
from . import g2_regex_terminal_genesis_v1 as primitive
from . import g2_werkzeug_guard_genesis_v1 as native

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
FROZEN_COMMIT="e40ff465b7a70bd55e56aeb0b40b57edd9aa7b0c"
FROZEN_PATH=U+"G2_THIRD_SOURCE_FINITE_TRANSFER_FROZEN_PREQUERY_V1.json"
ROLE_PREDECESSOR="57c400ea49881e440f7895acaeebeee5854363e3"
ROLE_PREDECESSOR_PATH=U+"G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
SCHEMA="G2_FROZEN_THIRD_SOURCE_REAL_NATIVE_FINITE_TRANSFER_V1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original_file(commit,path):
    return subprocess.check_output(["git","--no-replace-objects","-C",str(ROOT),
                                    "show",commit+":"+path],timeout=55)


def protocol():
    original=original_file(FROZEN_COMMIT,FROZEN_PATH)
    if original!=(ROOT/FROZEN_PATH).read_bytes():
        raise ValueError("UNKNOWN_FROZEN_SOURCE_ROLE_OR_POLICY_DRIFT")
    d=json.loads(original)
    if d["schema"]!="G2_THIRD_SOURCE_FINITE_TRANSFER_PREQUERY_V1":
        raise ValueError("UNKNOWN_UNREGISTERED_PROTOCOL")
    refs=json.loads(original_file(ROLE_PREDECESSOR,ROLE_PREDECESSOR_PATH))
    actual=refs["training_candidates"][2:]
    for new,old in zip(d["candidate_order"],actual):
        if any(new[q]!=old[q] for q in ("repo","pr","base","head","production","author_test")):
            raise ValueError("UNKNOWN_PREQUERY_NOT_FROM_ORIGINAL_METADATA_FREEZE")
    if len(actual)!=3 or len(d["candidate_order"])!=3:
        raise ValueError("UNKNOWN_SOURCE_POOL_SIZE")
    if len({x["repo"] for x in d["candidate_order"]})!=3:
        raise ValueError("UNKNOWN_SOURCE_DUPLICATE")
    return d


def source_pins():
    p=protocol();result={}
    for entry in p["immutable_method"]:
        b=(ROOT/entry["path"]).read_bytes()
        if b!=original_file(entry["commit"],entry["path"]):
            raise ValueError("UNKNOWN_FROZEN_OPERATION_CHANGED:"+entry["role"])
        digest=subprocess.check_output(["git","-C",str(ROOT),"hash-object","--stdin"],
                                       input=b,timeout=30).decode().strip()
        if digest!=entry["blob"]:
            raise ValueError("UNKNOWN_ORIGINAL_METHOD_BLOB_CHANGED:"+entry["role"])
        result[entry["role"]]=sha(b)
    return result


def safe_module_path(path):
    if (not isinstance(path,str) or not path.endswith(".py") or
        path.startswith("/") or "\x00" in path or "\\" in path or
        len(path)>256 or any(x in ("",".","..") for x in path.split("/")) or
        path.split("/")[0] in (".git",".github","tests","test","_tests") or
        any(x.startswith(".") for x in path.split("/"))):
        raise ValueError("UNKNOWN_SOURCE_PATH_NOT_CANONICAL")
    return True


def scope_from_imports(test_source,tracked,production,max_files):
    if not isinstance(test_source,bytes) or not isinstance(tracked,list):
        raise ValueError("UNKNOWN_AST_OR_TRACKED_SOURCE")
    if type(max_files) is not int or max_files<1 or max_files>8:
        raise ValueError("UNKNOWN_OBSERVATION_BUDGET")
    safe_module_path(production)
    if production not in tracked or len(set(tracked))!=len(tracked):
        raise ValueError("UNKNOWN_UNFROZEN_PRODUCTION_OR_DUPLICATE_TREE")
    for path in tracked:
        safe_module_path(path)
    tree=ast.parse(test_source)
    imports=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports.update(x.name for x in node.names)
        elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
            imports.add(node.module)
    found={production}
    for module in sorted(imports):
        segments=module.split(".")
        if (len(segments)<2 or
            segments[0] in sys.stdlib_module_names or
            not all(p.isidentifier() for p in segments)):
            continue
        suffix=segments[:-1]+[segments[-1]+".py"]
        choices=[path for path in tracked
                 if len(path.split("/"))>=len(suffix) and
                 path.split("/")[-len(suffix):]==suffix]
        if len(choices)>1:
            raise ValueError("UNKNOWN_SOURCE_MODULE_IDENTITY_AMBIGUOUS")
        if choices:
            found.add(choices[0])
    if len(found)>max_files:
        raise ValueError("UNKNOWN_SOURCE_IMPORT_SCOPE_CAP")
    return sorted(found)


def catalog(originals,max_edits=4):
    if not isinstance(originals,dict) or not originals:
        raise ValueError("UNKNOWN_EMPTY_ORIGINAL_SOURCE_WORLD")
    candidates=[]
    for path,blob in sorted(originals.items()):
        safe_module_path(path)
        if not isinstance(blob,bytes):
            raise ValueError("UNKNOWN_SOURCE_BLOB_NOT_BYTES")
        src=blob.decode("utf-8")
        local=learned.prepare_candidates(src)
        for i,c in enumerate(local):
            if not (isinstance(c["line"],int) and c["old"]!=c["new"] and
                    len(c["candidate_sha256"])==64):
                raise ValueError("UNKNOWN_UNQUALIFIED_ORIGINAL_PRIMITIVE")
            candidates.append({"path":path,"local_idx":i,"line":c["line"],
                "old":c["old"],"new":c["new"],"candidate_sha256":c["candidate_sha256"],
                "original_sha256":sha(blob),"family":"strict_terminal_anchor"})
    if len(candidates)>max_edits:
        raise ValueError("UNKNOWN_CANDIDATE_CAP_NOT_OUTCOME_SELECTED")
    return candidates


def mask_schedule(originals,candidates):
    count=len(candidates)
    if count>4:
        raise ValueError("UNKNOWN_MASK_BUDGET")
    worlds={}
    for mask in range(1<<count):
        current=dict(originals)
        for path,blob in sorted(originals.items()):
            ids=[j for j,c in enumerate(candidates) if c["path"]==path]
            chosen=[pos for pos,j in enumerate(ids) if mask&(1<<j)]
            if chosen:
                current[path]=learned.compose(
                    blob.decode("utf-8"),[candidates[j] for j in ids],chosen)
        if set(current)!=set(originals):
            raise ValueError("UNKNOWN_SOURCE_UNIVERSE_CHANGED")
        worlds[mask]=current
    return worlds


def source_fingerprint(world):
    return sha(json.dumps(
        {k:sha(v) for k,v in sorted(world.items())},
        sort_keys=True,separators=(",",":")).encode())


def native_cases(raw,selectors):
    if not isinstance(raw,bytes) or not isinstance(selectors,list) or not selectors:
        raise ValueError("UNKNOWN_ORIGINAL_PROTECTED_CASE_AUTHORITY")
    tree=ET.fromstring(raw)
    if tree.tag not in ("testsuites","testsuite"):
        raise ValueError("UNKNOWN_NATIVE_JUNIT_ROOT")
    patterns=[]
    for selector in selectors:
        bits=selector.split("::")
        path=bits[0]
        if (len(bits)<2 or not path.endswith(".py") or
            any(x in ("",".","..") for x in path.split("/")) or
            not all(x.isidentifier() for x in bits[1:])):
            raise ValueError("UNKNOWN_PROTECTED_AST_SELECTOR")
        patterns.append((Path(path).stem,bits[1:-1],bits[-1]))
    if len(set(map(str,patterns)))!=len(patterns):
        raise ValueError("UNKNOWN_DUPLICATE_PROTECTED_FUNCTION")
    counts=[0]*len(patterns)
    vector={}
    for row in tree.iter("testcase"):
        name=row.get("name","");classname=row.get("classname","")
        if not name or not classname:
            raise ValueError("UNKNOWN_INCOMPLETE_JUNIT_CASE_ID")
        matched=[]
        for i,(stem,classes,func) in enumerate(patterns):
            class_base=classname.split(".")
            if (stem in class_base and
                (not classes or class_base[-len(classes):]==classes) and
                (name==func or name.startswith(func+"[") and name.endswith("]"))):
                matched.append(i)
        if len(matched)!=1:
            raise ValueError("UNKNOWN_UNDECLARED_OR_AMBIGUOUS_ORIGINAL_CASE")
        tags=[c.tag for c in row]
        if any(tag not in ("failure",) for tag in tags):
            raise ValueError("UNKNOWN_ORIGINAL_NONEXECUTED_OR_MALFORMED_ASSERTION")
        identity=classname+"::"+name
        if identity in vector:
            raise ValueError("UNKNOWN_DUPLICATE_PARAMETRIZED_CASE")
        vector[identity]="FAIL" if "failure" in tags else "PASS"
        counts[matched[0]]+=1
    if not vector or not all(counts):
        raise ValueError("UNKNOWN_PROTECTED_FUNCTION_NOT_EXECUTED")
    return dict(sorted(vector.items()))


def finite_law(pass_masks,k,case_count):
    if (type(k) is not int or not 1<=k<=4 or
        type(case_count) is not int or not 1<=case_count<=256 or
        not isinstance(pass_masks,(list,tuple)) or len(pass_masks)!=(1<<k) or
        any(type(x) is not int or not 0<=x<=(1<<case_count)-1 for x in pass_masks)):
        raise ValueError("UNKNOWN_FINITE_CONSEQUENCE_TABLE")
    full=(1<<case_count)-1
    if pass_masks[0]==full or pass_masks[-1]!=full:
        raise ValueError("REJECTED_NO_SOURCE_DISTINCT_FULL_NATIVE_GAIN")
    for a in range(1<<k):
        for b in range(1<<k):
            if pass_masks[a|b]!=(pass_masks[a]|pass_masks[b]):
                raise ValueError("REJECTED_FINITE_JOIN_RELATION")
    wins=[mask for mask,x in enumerate(pass_masks) if x==full]
    best=min(wins,key=lambda mask:(mask.bit_count(),mask))
    for i in range(k):
        if best&(1<<i) and pass_masks[best^(1<<i)]==full:
            raise ValueError("REJECTED_CHOSEN_EDIT_UNNECESSARY")
    return {"pairs":(1<<k)**2,"selected_minimum_mask":best,
            "selected_necessary_edits":best.bit_count(),
            "source_subset_states":1<<k,"initial_pass_mask":pass_masks[0],
            "fully_repaired_mask":full}


def replay_choices(rows,k):
    if set(rows)!=set(range(1<<k)):
        raise ValueError("UNKNOWN_ORACLE_ROWS_MISSING")
    universe=set(rows[0])
    if not universe or any(set(v)!=universe or any(x not in ("FAIL","PASS") for x in v.values()) for v in rows.values()):
        raise ValueError("UNKNOWN_ORIGINAL_TEST_CASE_UNIVERSE")
    full=lambda v:all(x=="PASS" for x in v.values())
    masks=sorted(rows,key=lambda q:(q.bit_count(),q))
    best=next((q for q in masks if full(rows[q])),None)
    singles=next((q for q in masks if q.bit_count()==1 and full(rows[q])),None)
    # Frozen source-derived developmental greedy choice, never magically sees
    # unqueried native data without counting a charged oracle lookup.
    cursor=0;queried={0};greedy=None
    for step in range(k):
        if full(rows[cursor]):
            greedy=cursor;break
        remaining={n for n,v in rows[cursor].items() if v=="FAIL"}
        before_passing={n for n,v in rows[cursor].items() if v=="PASS"}
        opts=[]
        for j in range(k):
            if cursor&(1<<j):continue
            mask=cursor|(1<<j);queried.add(mask)
            new_remaining={n for n,v in rows[mask].items() if v=="FAIL"}
            new_passing={n for n,v in rows[mask].items() if v=="PASS"}
            if new_remaining<remaining and before_passing<=new_passing:
                opts.append((len(remaining-new_remaining),j,mask))
        if not opts:break
        opts.sort(key=lambda x:(-x[0],x[1]))
        cursor=opts[0][2]
    if full(rows[cursor]):
        greedy=cursor
    ledger_queries=next((i+1 for i,mask in enumerate(masks) if mask==best),len(masks))
    rel=("TIE_MINIMAL_MASK" if greedy==best and best is not None
         else "LEDGER_FINDABLE_COMPOSER_FAILED" if best is not None and greedy is None
         else "LEDGER_NO_SOLUTION" if best is None else "LEDGER_AT_LEAST_AS_POWERFUL")
    return {
        "prior_single":{"winner":singles,
           "minimum_native_case_oracle_calls":1+sum(q.bit_count()==1 for q in masks[:(
               next((i+1 for i,m in enumerate(masks) if m==singles),len(masks)))]
               )},
        "composed":{"winner":greedy,"oracle_masks_queried":sorted(queried),
                    "replay_charged_unique_native_calls":len(queried)},
        "ledger":{"winner":best,"fully_informed":True,
                  "oracle_masks_charged_until_minimal_solution":ledger_queries,
                  "all_source_masks_physically_executed":len(rows),
                  "unrestricted_to_single_edit":True},
        "relative_to_fully_informed_ledger":rel,
        "same_candidate_universe":True,
        "actual_agent":"NOT_EXECUTED",
        "G4":"UNKNOWN"}


def main(output, admission_one=None):
    if admission_one is None:
        admission_one=native_pool.one
    output=Path(output).absolute()
    if output.exists():
        raise ValueError("UNKNOWN_NONFRESH_EVIDENCE_DIR")
    output.mkdir(parents=True)
    started=time.monotonic()
    result={"schema":SCHEMA,"status":"UNKNOWN_NATIVE_NOT_EXECUTED","G2":"UNKNOWN",
        "G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
        "native_third_source":"NOT_ADMITTED","matched_ledger":"NOT_EXECUTED",
        "actual_agent":"NOT_EXECUTED","source_outcomes":[],"eligible":None,
        "natives_after_admission":0,"consequence_claim":"NOT_EXECUTED"}
    active=None;orig={}
    try:
        p=protocol()
        result["frozen_prequery_commit"]=FROZEN_COMMIT
        result["method_sha256"]=source_pins()
        for idx,task in enumerate(p["candidate_order"]):
            rec=admission_one({**task,"order":idx},idx,output/("admission-%02d"%idx))
            result["source_outcomes"].append(
                {k:v for k,v in rec.items() if k not in ("provisioning","traceback_tail")})
            (output/"ADMISSION_PROGRESS.json").write_text(
                json.dumps({"attempts":result["source_outcomes"],"G2":"UNKNOWN"},indent=2,sort_keys=True)+"\n")
            count=rec.get("native",{}).get("counts",{})
            if (rec.get("status")=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
                    and count.get("tests",0)>0 and count.get("failures",0)>0
                    and count.get("skipped")==count.get("errors")==0
                    and rec["native"]["returncode"]==1):
                result["eligible"]=task["repo"]+"#"+str(task["pr"])
                active=(task,rec,idx)
                break
        if not active:
            result["status"]="UNKNOWN_NO_GENUINE_NATIVE_FAILURE_IN_FROZEN_POOL"
            return result
        task,rec,idx=active
        result["native_third_source"]="ADMITTED_ORIGINAL_PROTECTED_NATIVE_FAIL"
        work=Path(rec["work_dir"]).resolve(strict=True)
        py=Path(rec["interpreter"])
        actual=work/task["production"]
        author=work/task["author_test"]
        if native_pool.git(work,"rev-parse","HEAD")!=task["base"]:
            raise ValueError("UNKNOWN_ORIGINAL_COMMIT_CHANGED")
        if sha(actual.read_bytes())!=rec["source_sha256"] or sha(author.read_bytes())!=rec["head_test_sha256"]:
            raise ValueError("UNKNOWN_ORIGINAL_OR_HEAD_AUTHOR_TEST_TAMPERED")
        original_junit=(output/("admission-%02d"%idx)/"native.xml").read_bytes()
        baseline=native_cases(original_junit,rec["protected_nodes"])
        if not any(q=="FAIL" for q in baseline.values()):
            raise ValueError("UNKNOWN_ADMISSION_NOT_TRULY_FAILING")
        result["original_native"]={"protected_cases":len(baseline),
                                  "passed":sum(q=="PASS" for q in baseline.values()),
                                  "failed":sum(q=="FAIL" for q in baseline.values()),
                                  "source_commit":task["base"],
                                  "test_head_sha256":rec["head_test_sha256"],
                                  "protected":rec["protected_nodes"],
                                  "junit_sha256":sha(original_junit)}
        raw=subprocess.check_output(["git","-C",str(work),"ls-files","-z"],timeout=60)
        tracked=[v.decode("utf-8") for v in raw.split(b"\0")
                 if v and v.endswith(b".py") and v.decode("utf-8").split("/")[0] not in ("tests","test","_tests")]
        import_scope=scope_from_imports(author.read_bytes(),tracked,task["production"],
                                        p["budgets"]["max_modules"])
        for name in import_scope:
            path=work/name
            if path.is_symlink() or not path.is_file():
                raise ValueError("UNKNOWN_SYMLINK_OR_ABSENT_DECLARED_SOURCE")
            data=path.read_bytes()
            if len(data)>2_000_000:
                raise ValueError("UNKNOWN_EXCESSIVE_SOURCE_BLOB")
            oid=subprocess.check_output(["git","-C",str(work),"rev-parse",
                                         task["base"]+":"+name],timeout=35).decode().strip()
            if subprocess.check_output(["git","-C",str(work),"hash-object","--stdin"],input=data,timeout=30).decode().strip()!=oid:
                raise ValueError("UNKNOWN_TRACKED_ORIGINAL_BLOB_NOT_VERIFIED")
            orig[name]=data
        result["scope"]={"files":import_scope,
                         "source_sha256":{k:sha(v) for k,v in sorted(orig.items())},
                         "source_from_metadata":task["production"],
                         "no_head_production_code_access":True}
        candidates=catalog(orig,max_edits=p["budgets"]["max_edits"])
        result["primitive_count"]=len(candidates)
        if not candidates:
            result["status"]="REJECTED_PROSPECTIVE_FROZEN_METHOD_INAPPLICABLE"
            result["matched_ledger"]="NO_CANDIDATES_IN_EQUAL_INFO_UNIVERSE"
            return result
        worlds=mask_schedule(orig,candidates)
        public=[{k:v for k,v in x.items() if k not in ()} for x in candidates]
        schedule={"schema":"G2_THIRD_SOURCE_SOURCE_MASKS_BEFORE_ANY_CANDIDATE_NATIVE",
             "frozen_protocol_commit":FROZEN_COMMIT,
             "method_blobs":result["method_sha256"],
             "original_native_source_repo":task["repo"],"native_author_test":task["author_test"],
             "original_junit_sha256":sha(original_junit),
             "source_scope":result["scope"],"candidates":public,
             "masks":{str(mask):{"source_sha256":{k:sha(v) for k,v in sorted(world.items())},
                  "fingerprint":source_fingerprint(world)} for mask,world in worlds.items()},
             "original_protected_cases":baseline}
        (output/"CANDIDATES_BEFORE_NATIVE.json").write_text(
            json.dumps(schedule,indent=2,sort_keys=True)+"\n")
        result["candidate_schedule_sha256"]=sha((output/"CANDIDATES_BEFORE_NATIVE.json").read_bytes())
        vectors={};times=[]
        test_path=task["author_test"];original_test=author.read_bytes()
        try:
            for mask,world in sorted(worlds.items()):
                if time.monotonic()-started>p["budgets"]["overall_seconds"]:
                    result["status"]="UNKNOWN_WALL_BUDGET_BEFORE_MASK_COMPLETE"
                    return result
                for path,data in world.items():
                    (work/path).write_bytes(data)
                if any((work/path).read_bytes()!=data for path,data in world.items()):
                    raise ValueError("UNKNOWN_SOURCE_EDIT_NOT_PHYSICALLY_APPLIED")
                changed={name for name,raw in world.items() if raw!=orig[name]}
                diff=set(native_pool.git(work,"diff","--name-only").splitlines())
                if diff!=changed|{test_path}:
                    raise ValueError("UNKNOWN_OUTSIDE_CHANGED_SOURCE_AND_AUTHOR_TEST_SCOPE")
                label="mask-%02d"%mask
                native_receipt=native.native(py,work,rec["protected_nodes"],label,output,120)
                result["natives_after_admission"]+=1
                if native_receipt["exit"] not in (0,1) or native_receipt["counts"].get("errors") or native_receipt["counts"].get("skipped"):
                    raise ValueError("UNKNOWN_MASK_NATIVE_APPARATUS:"+label)
                xml=(output/(label+".xml")).read_bytes()
                vector=native_cases(xml,rec["protected_nodes"])
                if set(vector)!=set(baseline) or native_receipt["counts"]["tests"]!=len(vector) or (
                    native_receipt["counts"]["failures"]!=sum(v=="FAIL" for v in vector.values())):
                    raise ValueError("UNKNOWN_ORIGINAL_PARAMETRIZED_CASE_UNIVERSE_CHANGED")
                if any(sha((work/path).read_bytes())!=sha(data) for path,data in world.items()) or (
                    author.read_bytes()!=original_test):
                    raise ValueError("UNKNOWN_ORIGINAL_NATIVE_MUTATED_SOURCE_OR_TEST")
                vectors[mask]=vector
                times.append(native_receipt["seconds"])
                result.setdefault("native_masks",{})[str(mask)]={
                    "case_verdict":vector,"source_fingerprint":source_fingerprint(world),
                    "junit_sha256":sha(xml),"native":native_receipt}
                for path,data in orig.items():
                    (work/path).write_bytes(data)
            if vectors[0]!=baseline:
                raise ValueError("UNKNOWN_BASELINE_NOT_REPRODUCIBLE")
            result["matched_ledger"]=replay_choices(vectors,len(candidates))
            test_names=sorted(baseline)
            pass_masks=[sum(1<<i for i,n in enumerate(test_names) if vectors[mask][n]=="PASS")
                        for mask in range(1<<len(candidates))]
            result["third_source_pass_masks"]=pass_masks
            try:
                result["finite_law"]=finite_law(pass_masks,len(candidates),len(test_names))
                result["consequence_claim"]="FINITE_JOIN_LAW_IN_ORIGINAL_NEW_SOURCE_NATIVE_CASES"
            except ValueError as exc:
                result["consequence_claim"]=str(exc)
                result["status"]="REJECTED_PROSPECTIVE_JOIN_OR_FULL_REPAIR"
                return result
            winning=result["finite_law"]["selected_minimum_mask"]
            if result["matched_ledger"]["ledger"]["winner"]!=winning:
                raise ValueError("UNKNOWN_MINIMAL_LEDGER_IDENTITY_MISMATCH")
            full_world=worlds[winning]
            for path,data in full_world.items():
                (work/path).write_bytes(data)
            for label in ("protected-repeat-a","protected-repeat-b"):
                rr=native.native(py,work,rec["protected_nodes"],label,output,120)
                result["natives_after_admission"]+=1
                vv=native_cases((output/(label+".xml")).read_bytes(),rec["protected_nodes"])
                if rr["exit"] or vv!={k:"PASS" for k in baseline}:
                    result["status"]="REJECTED_REPEATABILITY"
                    return result
                result.setdefault("repeat",[]).append({"label":label,"native":rr})
            entire=native.native(py,work,[test_path],"full-original-author",output,240)
            result["natives_after_admission"]+=1
            result["full_original_author_suite"]=entire
            if (entire["exit"]!=0 or entire["counts"]["tests"]<len(baseline)
                   or any(entire["counts"][x] for x in ("failures","errors","skipped"))):
                result["status"]="REJECTED_FULL_ORIGINAL_AUTHOR_TEST"
                return result
            for path,data in orig.items():
                (work/path).write_bytes(data)
            withdraw=native.native(py,work,rec["protected_nodes"],"physical-withdrawal",output,120)
            result["natives_after_admission"]+=1
            withdrawn=native_cases((output/"physical-withdrawal.xml").read_bytes(),rec["protected_nodes"])
            result["physical_withdrawal"]=withdraw
            if withdrawn!=baseline:
                result["status"]="REJECTED_NOT_CAUSAL"
                return result
            for path,data in full_world.items():
                (work/path).write_bytes(data)
            restored=native.native(py,work,rec["protected_nodes"],"physical-restoration",output,120)
            result["natives_after_admission"]+=1
            restored_vector=native_cases((output/"physical-restoration.xml").read_bytes(),rec["protected_nodes"])
            result["physical_restoration"]=restored
            if restored["exit"]!=0 or restored_vector!={n:"PASS" for n in baseline}:
                result["status"]="REJECTED_NOT_RESTORED"
                return result
            result["selected_source_sha256"]={k:sha(v) for k,v in full_world.items()}
            result["status"]="CANDIDATE_NEW_SOURCE_FINITE_TRANSFER_AWAITING_INDEPENDENT_AUDIT"
            result["G2"]="UNKNOWN"  # May be promoted only after independent source/JUnit audit.
            result["G4"]="UNKNOWN"  # Ledger always has the same finite candidate universe.
            return result
        finally:
            for path,data in orig.items():
                (work/path).write_bytes(data)
            if original_test!=author.read_bytes():
                result["status"]="UNKNOWN_ORIGINAL_HEAD_AUTHOR_TEST_TAMPERED"
            result["actual_native_mask_seconds"]=round(sum(times),4)
            result["actual_native_mask_calls"]=len(times)
            result["remaining_production_diff"]=native_pool.git(work,"diff","--name-only").splitlines()
    except Exception as error:
        result["status"]="UNKNOWN_EXPERIMENT_APPARATUS"
        result["reason"]=type(error).__name__+":"+str(error)[:750]
        result["traceback_tail"]=traceback.format_exc(limit=5)[-1500:]
        return result
    finally:
        result["wall_seconds"]=round(time.monotonic()-started,3)
        (output/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+"\n")
        print("NEW_THIRD_SOURCE",json.dumps({k:result.get(k) for k in (
            "status","eligible","primitive_count","natives_after_admission","G2","G4")},sort_keys=True),flush=True)


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.unified_consequence_runtime.g2_third_source_finite_transfer_v1 FRESH_OUTPUT_DIR")
    main(Path(sys.argv[1]))
