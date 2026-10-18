#!/usr/bin/env python3
"""Retrospective exposed Deer-flow: import-derived strict-regex finite composition.

No human-supplied winning repair, source line, second file, or grammar change.
This adapter maps parametrized JUnit cases, imports from original author test
and composes exact unchanged source-neutral primitive operations. It is not
a prospective G2 warrant, cannot unseal a new future, and trusts the native
author test and pinned source-owned Python runtime, not arbitrary-hostile code.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from . import g2_finite_composition_mistral_v2 as learned
from . import g2_regex_terminal_genesis_v1 as primitive
from . import g2_source_owned_uv_admission_v11 as source_owned
from . import g2_pool_first_native_failure_v1 as earlier

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
PROTO=U+"G2_DEER_IMPORT_COMPOSITION_V2_PROTOCOL.json"
SELECTOR=U+"G2_DEER_IMPORT_COMPOSITION_V2_SELECTOR_FREEZE.json"
PROTO_COMMIT="3e62cc3b225d18cdd23f1a3ed67d2ad82c460984"
SELECTOR_COMMIT="7fcaf3055980a11882f8c7649554e7ab3e458ddf"
SCHEMA="G2_EXPOSED_IMPORT_SCOPED_FINITE_MASK_NATIVE_V2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gitshow(commit,path):
    return subprocess.check_output(
        ["git","--no-replace-objects","-C",str(ROOT),"show",commit+":"+path],
        timeout=45)


def frozen():
    raw=(ROOT/PROTO).read_bytes()
    if raw!=gitshow(PROTO_COMMIT,PROTO):
        raise ValueError("UNKNOWN_FROZEN_EXPOSED_PROTOCOL_CHANGED")
    selector=(ROOT/SELECTOR).read_bytes()
    if selector!=gitshow(SELECTOR_COMMIT,SELECTOR):
        raise ValueError("UNKNOWN_FROZEN_MASK_SELECTOR_CHANGED")
    p=json.loads(raw);s=json.loads(selector)
    if (p["schema"]!="G2_DEERFLOW_EXPOSED_IMPORT_COMPOSITION_V2_PRETEST"
            or s["original_protocol_commit"]!=PROTO_COMMIT
            or p["status"]!="FROZEN_PROTOCOL_NOT_EXECUTED"
            or p["verdict"]["G2"]!="UNKNOWN"
            or s["prospective"].split(";")[0]!="RETROSPECTIVE_EXPOSED ONLY"):
        raise ValueError("UNKNOWN_PROTOCOL_SCOPE")
    for key,pathkey,commitkey in (
            ("method","generator_path","generator_commit"),
            ("method","composition_path","composition_commit"),
            ("dependencies","environment_file","environment_commit")):
        x=p[key]
        if (ROOT/x[pathkey]).read_bytes()!=gitshow(x[commitkey],x[pathkey]):
            raise ValueError("UNKNOWN_ORIGINAL_QUALIFIED_METHOD_CHANGED:"+x[pathkey])
    if p["method"]["maximum_candidates"]!=3 or p["native_cases"]["baseline_failures"]!=2:
        raise ValueError("UNKNOWN_DECLARED_EXPOSED_BUDGET")
    return p


def _parts(selector):
    if not isinstance(selector,str) or selector.count("::")<1:
        raise ValueError("UNKNOWN_ORIGINAL_PROTECTED_SELECTOR")
    pathname,*parts=selector.split("::")
    path=PurePosixPath(pathname)
    if (not pathname.startswith("backend/tests/") or
        not pathname.endswith(".py") or
        any(x in (".","..","") for x in pathname.split("/")) or
        not parts or any(not p.isidentifier() for p in parts)):
        raise ValueError("UNKNOWN_INVALID_PROTECTED_SELECTOR")
    module=".".join(path.with_suffix("").parts[1:])
    return module,parts[:-1],parts[-1]


def parse_native_cases(raw,selectors):
    """Case-wise full JUnit classname/name vector; never one-case-per-function."""
    if not isinstance(raw,(str,bytes)) or not selectors:
        raise ValueError("UNKNOWN_NATIVE_JUNIT_INPUT")
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as err:
        raise ValueError("UNKNOWN_NATIVE_JUNIT_PARSE") from err
    if root.tag not in ("testsuites","testsuite"):
        raise ValueError("UNKNOWN_JUNIT_ROOT")
    expected=[_parts(x) for x in selectors]
    if len(set(map(str,expected)))!=len(expected):
        raise ValueError("UNKNOWN_DUPLICATE_PROTECTED_FUNCTION")
    result={};coverage=[0]*len(expected)
    cases=list(root.iter("testcase"))
    if not cases:raise ValueError("UNKNOWN_NO_NATIVE_CASES")
    for c in cases:
        name=c.attrib.get("name","")
        classname=c.attrib.get("classname","")
        if not name or not classname:
            raise ValueError("UNKNOWN_MISSING_JUNIT_CASE_IDENTITY")
        matched=[]
        for i,(mod,classes,func) in enumerate(expected):
            expected_class=mod+("."+ ".".join(classes) if classes else "")
            if (classname==expected_class and
                (name==func or (name.startswith(func+"[") and name.endswith("]")))):
                matched.append(i)
        if len(matched)!=1:
            raise ValueError("UNKNOWN_UNDECLARED_OR_AMBIGUOUS_NATIVE_CASE")
        if len(tuple(c.iter("error"))) or len(tuple(c.iter("skipped"))):
            raise ValueError("UNKNOWN_NATIVE_ERROR_SKIP_XFAIL")
        if any(el.tag not in ("failure",) for el in c):
            raise ValueError("UNKNOWN_NATIVE_UNRECOGNIZED_JUNIT_STATUS")
        label=classname+"::"+name
        if label in result:
            raise ValueError("UNKNOWN_DUPLICATE_PARAMETRIZED_NATIVE_CASE")
        result[label]="FAIL" if any(el.tag=="failure" for el in c) else "PASS"
        coverage[matched[0]]+=1
    if not all(coverage):
        raise ValueError("UNKNOWN_MISSING_CHANGED_AUTHOR_FUNCTION_CASE")
    return dict(sorted(result.items()))


def _safe_source_path(path):
    if not isinstance(path,str) or not path.endswith(".py") or "\x00" in path or "\\" in path:
        raise ValueError("UNKNOWN_ORIGINAL_TRACKED_SOURCE_PATH")
    parts=path.split("/")
    if path.startswith("/") or any(p in (".","..","") for p in parts):
        raise ValueError("UNKNOWN_ORIGINAL_TRACKED_SOURCE_PATH")
    if not path.startswith("backend/"):
        raise ValueError("UNKNOWN_OUTSIDE_SOURCE_OWNED_BACKEND")
    return parts


def imported_source_module_files(test_bytes, tracked_paths, production_path,max_modules):
    """Only AST import ancestry, unique verified tracked path -> observed module."""
    if not isinstance(max_modules,int) or isinstance(max_modules,bool) or max_modules<1:
        raise ValueError("UNKNOWN_IMPORT_BUDGET")
    if not isinstance(test_bytes,bytes):
        raise ValueError("UNKNOWN_AUTHOR_TEST_SOURCE_NOT_BYTES")
    tree=ast.parse(test_bytes)
    imports=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            if node.level==0 and node.module:
                imports.add(node.module)
        elif isinstance(node,ast.Import):
            imports.update(item.name for item in node.names)
    if len(imports)>max_modules:
        raise ValueError("UNKNOWN_SOURCE_OBSERVATION_TOO_MANY_IMPORTS")
    if len(set(tracked_paths))!=len(tracked_paths):
        raise ValueError("UNKNOWN_DUPLICATE_TRACKED_SOURCE")
    raw_paths={p:_safe_source_path(p) for p in tracked_paths}
    if production_path not in raw_paths:
        raise ValueError("UNKNOWN_MISSING_FROZEN_PRODUCTION")
    discovered={}
    for module in sorted(imports):
        if not all(p.isidentifier() for p in module.split(".")):
            raise ValueError("UNKNOWN_UNSAFE_OR_NONCANONICAL_PYTHON_MODULE")
        components=module.split(".")
        # A bare import (e.g. stdlib 'types') has no source-owned package
        # lineage: matching every tracked file named types.py is unsound.
        # Only explicit original package-qualified import paths are admitted
        # as a source-to-observation binding in this versioned V2 interface.
        if len(components)<2:
            continue
        suffix=components[:-1]+[components[-1]+".py"]
        candidates=[path for path,parts in raw_paths.items()
                    if len(parts)>=len(suffix) and parts[-len(suffix):]==suffix]
        if len(candidates)>1:
            raise ValueError("UNKNOWN_AMBIGUOUS_SOURCE_MODULE_IDENTITY:"+module)
        if candidates:
            discovered[candidates[0]]=module
    if production_path not in discovered:
        raise ValueError("UNKNOWN_ORIGINAL_PRODUCTION_NOT_IMPORT_REACHABLE")
    return sorted(discovered)


def source_catalog(originals,imported):
    """Use unchanged independently qualified regex generator, no new patterns."""
    if not imported or not isinstance(originals,dict):
        raise ValueError("UNKNOWN_EMPTY_OBSERVATION_SOURCE")
    found=[]
    for path in sorted(imported):
        _safe_source_path(path)
        raw=originals[path]
        if not isinstance(raw,bytes):
            raise ValueError("UNKNOWN_ORIGINAL_SOURCE_ENCODING")
        content=raw.decode("utf-8")
        primitives=learned.prepare_candidates(content)
        for local_idx,row in enumerate(primitives):
            # Keep the exact previous source primitive, not a target-crafted
            # patch or a new form of whole-input operation.
            if not (row["old"]!=row["new"] and row["line"]>0):
                raise ValueError("UNKNOWN_PRIMITIVE_SOURCE_BOUND")
            found.append({"path":path,"local_idx":local_idx,"line":row["line"],
                          "old":row["old"],"new":row["new"],
                          "candidate_sha256":row["candidate_sha256"],
                          "original_source_sha256":sha(raw),
                          "family":"strict_terminal_anchor"})
    return found


def render_mask(originals,catalog,mask):
    k=len(catalog)
    if type(mask) is not int or mask<0 or mask>=1<<k:
        raise ValueError("UNKNOWN_SOURCE_MASK")
    output=dict(originals)
    for path,source in originals.items():
        positions=[i for i,c in enumerate(catalog) if c["path"]==path]
        slots=[catalog[i] for i in positions]
        # Global subset bits index across files; compose() indexes only the
        # selected file's local candidate sequence. Neither is an outcome-
        # dependent winner index, and no primitive edit has been changed.
        local=[j for j,i in enumerate(positions) if mask & (1<<i)]
        if local:
            output[path]=learned.compose(source.decode("utf-8"),slots,local)
    if set(output)!=set(originals):
        raise ValueError("UNKNOWN_SOURCE_PATH_UNIVERSE")
    return output


def evaluate_lattice(table,k):
    if (type(k) is not int or k<1 or k>3 or
        set(table)!=set(range(1<<k))):
        raise ValueError("UNKNOWN_INCOMPLETE_FINITE_MASK_TABLE")
    baseline=table[0]
    if not (isinstance(baseline,dict) and 4<=len(baseline)<=24 and
            set(baseline.values())=={"PASS","FAIL"}):
        raise ValueError("UNKNOWN_INADMISSIBLE_BASELINE_CASES")
    for m,vec in table.items():
        if (not isinstance(vec,dict) or set(vec)!=set(baseline)
                or any(x not in ("PASS","FAIL") for x in vec.values())):
            raise ValueError("UNKNOWN_CASE_IDENTITY_OR_ORACLE_INCOMPLETE")
    for x in table:
        have={n for n,v in table[x].items() if v=="PASS"}
        for y in table:
            if x & y == x:
                later={n for n,v in table[y].items() if v=="PASS"}
                if not have<=later:
                    return {"status":"UNKNOWN_NONMONOTONE_FINITE_CONSEQUENCES",
                            "selected_mask":None,"fully_informed_ledger":"NOT_RUN"}
    winners=[x for x in table if all(v=="PASS" for v in table[x].values())]
    if not winners:
        return {"status":"REJECTED_NO_COMPLETE_FINITE_REPAIR",
                "selected_mask":None,"fully_informed_ledger":"NO_CLOSING_MASK"}
    selected=min(winners,key=lambda x:(x.bit_count(),x))
    if selected==0 or any(
            all(v=="PASS" for v in table[selected^(1<<i)].values())
            for i in range(k) if selected&(1<<i)):
        return {"status":"UNKNOWN_EDIT_CAUSALITY_NOT_NECESSARY",
                "selected_mask":None,"fully_informed_ledger":"NOT_RUN"}
    return {"status":"WARRANTED_FINITE_TABLE_SOURCE_NEUTRAL",
            "selected_mask":selected,
            "fully_informed_ledger":"TIE_EQUAL_INFORMATION",
            "selected_edit_count":selected.bit_count(),
            "table_scope":"ORIGINAL_SOURCE_ONLY_FINITE_AUTHOR_TESTS"}


def _tracked(work):
    raw=subprocess.check_output(["git","-C",str(work),"ls-files","-z"],timeout=40)
    return [p.decode("utf-8") for p in raw.split(b"\0") if p and p.endswith(b".py") and p.startswith(b"backend/")]


def _git_diff(work):
    d=subprocess.check_output(["git","-C",str(work),"diff","--name-only"],text=True,timeout=40)
    return set(d.splitlines())


def _verify_original(work,originals,test,path,test_sha):
    if sha((work/test).read_bytes())!=test_sha:
        raise ValueError("UNKNOWN_CHANGED_AUTHOR_TEST_SOURCE")
    if any(sha((work/p).read_bytes())!=sha(b) for p,b in originals.items()):
        raise ValueError("UNKNOWN_SOURCE_NOT_RESTORED")
    if _git_diff(work)!={test}:
        raise ValueError("UNKNOWN_UNAUTHORIZED_GIT_SOURCE_DELTA")
    if (work/path).is_symlink():
        raise ValueError("UNKNOWN_ORIGINAL_PRODUCTION_SYMLINK")


def _native(py,project,selectors,output,label,reference):
    junit=output/(label+".xml")
    stdout=output/(label+".stdout")
    stderr=output/(label+".stderr")
    rel=[s.split("/",1)[1] if s.startswith("backend/") else s for s in selectors]
    cmd=[str(py),"-m","pytest","-q","--junitxml="+str(junit),*rel]
    start=time.monotonic()
    try:
        done=subprocess.run(cmd,cwd=project,text=True,capture_output=True,timeout=160,
            env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
                 "PYTHONPATH":str(project)+os.pathsep+os.environ.get("PYTHONPATH","")})
    except subprocess.TimeoutExpired as exc:
        raise ValueError("UNKNOWN_ORIGINAL_NATIVE_TIMEOUT") from exc
    stdout.write_text(done.stdout);stderr.write_text(done.stderr)
    if not junit.is_file():
        raise ValueError("UNKNOWN_MISSING_NATIVE_JUNIT")
    vec=parse_native_cases(junit.read_bytes(),selectors)
    if set(vec)!=set(reference):
        raise ValueError("UNKNOWN_PARAMETRIZED_NATIVE_CASE_DRIFT")
    if done.returncode != (0 if all(s=="PASS" for s in vec.values()) else 1):
        raise ValueError("UNKNOWN_NATIVE_EXIT_CONSEQUENCE_MISMATCH")
    return {"status":"WARRANTED_SCOPED_ORIGINAL_NATIVE_JUNIT",
            "returncode":done.returncode,"elapsed_seconds":round(time.monotonic()-start,4),
            "counts":{"tests":len(vec),"failures":sum(x=="FAIL" for x in vec.values()),
                      "errors":0,"skipped":0},
            "junit_sha256":sha(junit.read_bytes()),"stdout_sha256":sha(stdout.read_bytes()),
            "stderr_sha256":sha(stderr.read_bytes()),"vector":vec}


def main(output):
    output=Path(output).absolute()
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    result={"schema":SCHEMA,"science":"EXPOSED_ONLY_NOT_G2",
       "status":"UNKNOWN_NOT_EXECUTED","original_future_status":"OPENED_PRIOR_TO_THIS_EXPERIMENT",
       "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
       "Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
       "agent_comparator":"NOT_EXECUTED","reused_frozen_primitive":True,
       "native_calls":0,"source_candidates":[],"masks":{}}
    work=None;originals=None;author_path=None
    try:
        p=frozen()
        task=p["original"]
        role={k:task[v] for k,v in [
            ("repo","repo"),("pr","pr"),("base","base"),("head","head"),
            ("production","source"),("author_test","test")]}
        if p["original"]["current_source_state"]!="ALREADY_EXPOSED":
            raise ValueError("UNKNOWN_FUTURE_SCOPE_RELABEL")
        rec=source_owned.one(role,0,output/"source-owned-native-original")
        result["original_admission"]={k:v for k,v in rec.items() if k!="source_declared_dependency_sync"}
        result["native_calls"]+=1 if rec.get("native") else 0
        if rec.get("status")!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            result["status"]="UNKNOWN_ORIGINAL_NATIVE_NOT_ADMITTED_"+rec.get("status","NO_STATUS")
            return result
        if rec["source_sha256"]!=task["source_sha256"] or rec["head_test_sha256"]!=task["test_sha256"]:
            raise ValueError("UNKNOWN_HISTORIC_PROSPECTIVE_SOURCE_IDENTITY")
        work=Path(rec["work_dir"])
        author_path=task["test"]
        project=work/rec["project_root"]
        py=Path(rec["interpreter"])
        selectors=rec["protected_nodes"]
        if (len(selectors)!=2 or rec["native"]["counts"]!={"tests":4,"failures":2,
                   "errors":0,"skipped":0}):
            raise ValueError("UNKNOWN_HISTORIC_NATIVE_PROTECTED_COUNTS")
        reference=parse_native_cases((output/"source-owned-native-original/native.xml").read_bytes(),selectors)
        if len(reference)!=4 or sum(x=="FAIL" for x in reference.values())!=2:
            raise ValueError("UNKNOWN_REAL_NATIVE_PARAMETRIZATION")
        result["original_vector"]=reference
        tracked=_tracked(work)
        imported=imported_source_module_files((work/author_path).read_bytes(),
             tracked,task["source"],p["method"]["maximum_modules"])
        result["imported_original_source_files"]=imported
        # The file cap applies to grammar-eligible mutation files, not to
        # harmless imported project modules. The distinct module-observation
        # limit was already checked before this (<=30 source imports).
        originals={}
        for path in imported:
            f=work/path
            if f.is_symlink() or not f.is_file():
                raise ValueError("UNKNOWN_NONREGULAR_IMPORTED_ORIGINAL_SOURCE")
            orig=f.read_bytes()
            baseline=subprocess.check_output(["git","-C",str(work),"show",
                task["base"]+":"+path],timeout=35)
            if orig!=baseline:
                raise ValueError("UNKNOWN_IMPORT_SOURCE_NOT_ORIGINAL")
            originals[path]=orig
        catalog=source_catalog(originals,imported)
        eligible_paths={c["path"] for c in catalog}
        result["eligible_original_source_files"]=sorted(eligible_paths)
        if len(eligible_paths)>p["method"]["maximum_eligible_files"]:
            result["status"]="UNKNOWN_GRAMMAR_ELIGIBLE_SOURCE_FILES_CAP"
            return result
        result["candidate_count"]=len(catalog)
        if len(catalog)>p["method"]["maximum_candidates"]:
            result["status"]="UNKNOWN_SOURCE_NEUTRAL_CANDIDATE_CAP"
            return result
        result["source_candidates"]=[
           {k:v for k,v in c.items() if k not in ("old","new")}
           for c in catalog]
        # These plans are archived BEFORE any edited-source native test.
        planned=[{"mask":m,"source_sha256":{
            path:sha(b) for path,b in render_mask(originals,catalog,m).items()}}
            for m in range(1<<len(catalog))]
        (output/"CANDIDATES_BEFORE_NATIVE.json").write_text(
            json.dumps({"original_source_sha256":{k:sha(v) for k,v in originals.items()},
                         "candidates":result["source_candidates"],"masks":planned},
                       indent=2,sort_keys=True)+"\n")
        if not catalog:
            result["status"]="REJECTED_FROZEN_REGEX_GRAMMAR_SOURCE_INAPPLICABLE"
            return result
        k=len(catalog)
        if k>3:raise ValueError("UNKNOWN_FINITE_MASK_ENVELOPE")
        for mask in range(1<<k):
            trial=render_mask(originals,catalog,mask)
            for path,source in trial.items():
                (work/path).write_bytes(source)
            try:
                observed=_native(py,project,selectors,output,"mask-%02d"%mask,reference)
                result["native_calls"]+=1
                result["masks"][str(mask)]={
                   "mask":mask,"source_sha256":{path:sha(raw) for path,raw in trial.items()},
                   "native":observed}
            finally:
                for path,data in originals.items():
                    (work/path).write_bytes(data)
                _verify_original(work,originals,author_path,task["source"],task["test_sha256"])
        table={int(i):x["native"]["vector"] for i,x in result["masks"].items()}
        verdict=evaluate_lattice(table,k)
        result["finite_lattice"]=verdict
        if verdict["status"]!="WARRANTED_FINITE_TABLE_SOURCE_NEUTRAL":
            result["status"]=verdict["status"]
            return result
        chosen=verdict["selected_mask"]
        final_sources=render_mask(originals,catalog,chosen)
        for path,data in final_sources.items():
            (work/path).write_bytes(data)
        try:
            a=_native(py,project,selectors,output,"selected-repeat-a",reference)
            b=_native(py,project,selectors,output,"selected-repeat-b",reference)
            result["native_calls"]+=2
            if a["vector"]!=b["vector"] or not all(x=="PASS" for x in a["vector"].values()):
                result["status"]="REJECTED_UNSTABLE_PROTECTED_REPAIR"
                return result
            result["protected_repeat"]=[a,b]
            # Full author regression covers all tests in the original HEAD
            # author test file, without editing/replacing it.
            all_tests=output/"complete-author.xml"
            t=time.monotonic()
            cmd=[str(py),"-m","pytest","-q","--junitxml="+str(all_tests),
                 str(Path(author_path).relative_to(Path(rec["project_root"])))]
            q=subprocess.run(cmd,cwd=project,text=True,capture_output=True,timeout=240,
                env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
                     "PYTHONPATH":str(project)+os.pathsep+os.environ.get("PYTHONPATH","")})
            result["native_calls"]+=1
            (output/"complete-author.stdout").write_text(q.stdout)
            (output/"complete-author.stderr").write_text(q.stderr)
            if not all_tests.exists():
                raise ValueError("UNKNOWN_NO_FULL_AUTHOR_JUNIT")
            report=ET.fromstring(all_tests.read_bytes())
            cases=list(report.iter("testcase"))
            errors=sum(bool(tuple(c.iter("error"))) for c in cases)
            skipped=sum(bool(tuple(c.iter("skipped"))) for c in cases)
            failures=sum(bool(tuple(c.iter("failure"))) for c in cases)
            result["full_author"]={"tests":len(cases),"failures":failures,
                                   "skipped":skipped,"errors":errors,
                                   "returncode":q.returncode,
                                   "seconds":round(time.monotonic()-t,4),
                                   "junit_sha256":sha(all_tests.read_bytes())}
            if (q.returncode!=0 or len(cases)<=len(reference) or
                    failures or errors or skipped):
                result["status"]="REJECTED_SELECTED_REPAIR_FULL_AUTHOR"
                return result
        finally:
            for path,data in originals.items():
                (work/path).write_bytes(data)
            _verify_original(work,originals,author_path,task["source"],task["test_sha256"])
        # Physical all-source withdrawal: absence of every chosen edit must
        # restore each original parametrized failure identity.
        removed=_native(py,project,selectors,output,"physical-all-withdrawal",reference)
        result["native_calls"]+=1
        result["withdrawal"]=removed
        if removed["vector"]!=reference:
            result["status"]="UNKNOWN_WITHDRAWAL_NOT_CAUSALLY_RESTORED"
            return result
        for path,data in final_sources.items():
            (work/path).write_bytes(data)
        try:
            restored=_native(py,project,selectors,output,"physical-all-restoration",reference)
            result["native_calls"]+=1
            result["restoration"]=restored
            if any(v!="PASS" for v in restored["vector"].values()):
                result["status"]="UNKNOWN_RESTORATION_NOT_REPAIRED"
                return result
            result["status"]="CANDIDATE_EXPOSED_NATIVE_IMPORT_COMPOSITION_AWAITING_INDEPENDENT_AUDIT"
            result["selected_mask"]=chosen
            result["informed_ledger"]="SAME_FINITE_TABLE_SAME_MINIMAL_MASK_TIE_NOT_SEPARATE_AGENT_RUN"
            result["no_prospective_transfer"]=True
            result["G2"]="UNKNOWN"
            return result
        finally:
            for path,data in originals.items():
                (work/path).write_bytes(data)
            _verify_original(work,originals,author_path,task["source"],task["test_sha256"])
    except Exception as err:
        result["status"]="UNKNOWN_EXECUTION_APPARATUS"
        result["error"]=type(err).__name__+":"+str(err)[:600]
        result["traceback_tail"]=traceback.format_exc(limit=7)[-1700:]
        return result
    finally:
        result["elapsed_seconds"]=round(time.monotonic()-started,3)
        (output/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:result.get(k) for k in
            ("status","G2","candidate_count","selected_mask","native_calls","elapsed_seconds")},sort_keys=True))


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.unified_consequence_runtime.g2_deer_import_composition_v2 FRESH_OUTPUT")
    main(Path(sys.argv[1]))
