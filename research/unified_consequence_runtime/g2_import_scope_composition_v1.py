#!/usr/bin/env python3
"""Exposed-source ONLY: importer-scoped multi-file finite repair composition.

Never an untouched prospective future. Operation primitive frozen at V1; only
source-file scope and parameterized outcome representation are developed here.
"""
from __future__ import annotations
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib
import traceback
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import g2_source_owned_uv_admission_v11 as owner
from research.unified_consequence_runtime import g2_regex_terminal_genesis_v1 as primitive
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
PROTOCOL_COMMIT="4ce42422ce3310995f324863062438a49dafbb4f"
PRIMITIVE_COMMIT="d45288833a13b1ddf6afde01c0b89a84bfc7ce32"
ADAPTER_COMMIT="fd932d730744b0fb5528f74caeafe99ab13bf9fa"
SOURCE_BASE="e2feca1e567d9bafce657de8ad8bc668bd7ad513"
TEST_HEAD="cd9c12bb89c0c9d727a348b5fba3bd95730a9186"
MAX_FILES=24
MAX_CANDIDATES=12
MAX_TRIALS=18
MAX_PARTS=3
TIMEOUT_NATIVE=160

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def frozen(rev,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",rev+":"+path],timeout=55)

def preflight():
    p=U+"G2_IMPORT_SCOPED_COMPOSITION_V1_PROTOCOL_20261019.md"
    assert (ROOT/p).read_bytes()==frozen(PROTOCOL_COMMIT,p),"DEVELOPMENT_PROTOCOL_CHANGED"
    p=U+"g2_regex_terminal_genesis_v1.py"
    assert (ROOT/p).read_bytes()==frozen(PRIMITIVE_COMMIT,p),"ORIGINAL_PRIMITIVE_CHANGED"
    p=U+"g2_source_owned_uv_admission_v11.py"
    assert (ROOT/p).read_bytes()==frozen(ADAPTER_COMMIT,p),"SOURCE_OWNED_NATIVE_APPARATUS_CHANGED"
    return {"repo":"bytedance/deer-flow","pr":5960,"base":SOURCE_BASE,"head":TEST_HEAD,
        "production":"backend/app/gateway/routers/agents.py",
        "author_test":"backend/tests/test_custom_agent.py"}

def source_scope(work:Path,task:dict,project:Path):
    """Derive local import owned source files from original head-author test."""
    head_test=(work/task["author_test"]).read_text()
    tree=ast.parse(head_test)
    imports=sorted({node.module for node in ast.walk(tree)
                    if isinstance(node,ast.ImportFrom) and node.module
                    and not node.level})
    pyproject=tomllib.loads((project/"pyproject.toml").read_text())
    members=pyproject.get("tool",{}).get("uv",{}).get("workspace",{}).get("members",[])
    assert isinstance(members,list)
    roots=[project]+[project/member for member in members]
    sources={task["production"]}
    for dotted in imports:
        relative=Path(*dotted.split("."))
        for root in roots:
            for suffix in (relative.with_suffix(".py"),relative/"__init__.py"):
                selected=(root/suffix).resolve()
                if not selected.is_relative_to(work.resolve()) or not selected.is_file():
                    continue
                path=selected.relative_to(work).as_posix()
                if "/tests/" in "/"+path+"/" or path==task["author_test"]:
                    continue
                try:
                    pool.git(work,"ls-files","--error-unmatch",path)
                except Exception:
                    continue
                sources.add(path)
    chosen=sorted(sources)
    assert 1<=len(chosen)<=MAX_FILES,"IMPORT_SOURCE_UNIVERSE_BUDGET"
    return chosen,imports

def candidate_catalog(work,scope):
    catalog=[]
    originals={}
    for p in scope:
        raw=(work/p).read_bytes()
        originals[p]=raw
        s=raw.decode("utf-8")
        pieces=s.splitlines(keepends=True)
        for item in primitive.enumerate_candidates(s):
            if item["kind"]!="strict_terminal_anchor":
                continue
            line=item["line"]
            before=item["old_expr"];after=item["new_expr"]
            if not 1<=line<=len(pieces) or pieces[line-1].count(before)!=1:
                continue
            updated=pieces.copy()
            updated[line-1]=updated[line-1].replace(before,after,1)
            if "".join(updated)!=item["_edited"]:
                continue
            catalog.append({"path":p,"line":line,"old":before,"new":after,
                "primitive_sha256":item["candidate_sha256"],
                "bytes_added":item["bytes_added"]})
    catalog.sort(key=lambda c:(abs(c["bytes_added"]),c["path"],c["line"]))
    if len(catalog)>MAX_CANDIDATES:
        return originals,[], "UNKNOWN_CANDIDATE_CATALOG_OVER_BUDGET"
    assert len({(x["path"],x["line"]) for x in catalog})==len(catalog),"OVERLAPPING_LITERAL_SITES"
    return originals,catalog,"CANDIDATE_CATALOG_ADMITTED"

def render_sources(originals,catalog,selected):
    edits={}
    for idx in selected:
        c=catalog[idx]
        edits.setdefault(c["path"],[]).append(c)
    rendered={}
    for path,raw in originals.items():
        if path not in edits:
            continue
        lines=raw.decode().splitlines(keepends=True)
        for edit in sorted(edits[path],key=lambda t:t["line"]):
            ix=edit["line"]-1
            assert lines[ix].count(edit["old"])==1,("NONUNIQUE_OR_MISSING_SITE",path,ix)
            lines[ix]=lines[ix].replace(edit["old"],edit["new"],1)
        updated="".join(lines)
        ast.parse(updated,filename=path)
        compile(updated,path,"exec")
        rendered[path]=updated.encode("utf-8")
    return rendered

def patch_world(work,originals,rendered,test_path):
    for path,raw in originals.items():
        (work/path).write_bytes(rendered.get(path,raw))
    actual=sorted(pool.git(work,"diff","--name-only").splitlines())
    expected=sorted([test_path]+[path for path in rendered if rendered[path]!=originals[path]])
    assert actual==expected,("SCOPE_VIOLATION",actual,expected)
    for path,raw in rendered.items():
        assert (work/path).read_bytes()==raw

def vector_xml(path):
    names={}
    for item in ET.parse(path).getroot().iter("testcase"):
        key=(item.attrib.get("classname","")+"::"+item.attrib.get("name",""))
        assert key not in names and item.attrib.get("name"),"DUPLICATE_CASE"
        tags={v.tag for v in item}
        names[key]="ERROR" if "error" in tags else "SKIP" if "skipped" in tags else (
                "FAIL" if "failure" in tags else "PASS")
    assert names
    return names

def one_native(work,project,python,protected,output,label,whole_file=False):
    junit=output/(label+".xml")
    log=output/(label+".log")
    rel=project.relative_to(work)
    if whole_file:
        args=[str(Path(protected[0].split("::")[0]).relative_to(rel))]
    else:
        args=[str(Path(n.split("::")[0]).relative_to(rel))+"::"+"::".join(n.split("::")[1:])
              for n in protected]
    argv=[str(python),"-m","pytest","-q","--junitxml="+str(junit),*args]
    start=time.monotonic()
    try:
        p=subprocess.run(argv,cwd=project,text=True,capture_output=True,timeout=TIMEOUT_NATIVE,
            env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
                 "PYTHONPATH":str(project)+os.pathsep+os.environ.get("PYTHONPATH","")})
        code,stdout,stderr=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as e:
        code,stdout,stderr=124,str(e.stdout or ""),str(e.stderr or "TIMEOUT")
    payload={"argv":argv,"returncode":code,"stdout":stdout,"stderr":stderr}
    log.write_text(json.dumps(payload,sort_keys=True)+"\n")
    v=vector_xml(junit) if junit.is_file() else {}
    counts={"tests":len(v),"failures":sum(x=="FAIL" for x in v.values()),
            "errors":sum(x=="ERROR" for x in v.values()),
            "skipped":sum(x=="SKIP" for x in v.values())}
    return {"exit":code,"verdicts":v,"counts":counts,
        "log_sha256":digest(log.read_bytes()),
        "junit_sha256":digest(junit.read_bytes()) if junit.is_file() else None,
        "elapsed_seconds":round(time.monotonic()-start,3)}

def checked(native,expected):
    assert native["counts"]["tests"]==len(expected),"CHANGED_TEST_SET_SIZE"
    assert set(native["verdicts"])==set(expected),"CHANGED_NATIVE_TEST_CASE_IDS"
    assert native["counts"]["errors"]==0 and native["counts"]["skipped"]==0,"UNTRUSTWORTHY_NATIVE_CASE"
    assert native["exit"] in (0,1),"ORIGINAL_PYTEST_PROCESS_FAILED"

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"G2_EXPOSED_IMPORT_SCOPED_FINITE_COMPOSITION_V1",
            "status":"UNKNOWN_NATIVE_APPARATUS","epistemic":"RETROSPECTIVE_DEVELOPMENT_ONLY",
            "G2":"UNKNOWN","G4":"UNKNOWN","future":"ALREADY_OPENED",
            "Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
            "candidates":[],"trials":[],"subsets":{},"selected":[]}
    start=time.monotonic()
    work=None;originals=None;task=None
    try:
        task=preflight()
        admission=owner.one(task,0,out/"original-author-admission")
        report["original_admission"]={k:v for k,v in admission.items()
                                       if k!="source_declared_dependency_sync"}
        if admission["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"]="UNKNOWN_ORIGINAL_NOT_ADMITTED_"+admission["status"]
            return
        assert admission["native"]["counts"]=={"tests":4,"failures":2,"errors":0,"skipped":0}
        work=Path(admission["work_dir"])
        project=work/admission["project_root"]
        python=Path(admission["interpreter"])
        original_xml=out/"original-author-admission/native.xml"
        before=vector_xml(original_xml)
        assert len(before)==4 and list(before.values()).count("FAIL")==2
        report["original_verdicts"]=before
        scope,imports=source_scope(work,task,project)
        report["source_scope"]=scope
        report["test_import_modules_checked"]=len(imports)
        originals,catalog,metadata_status=candidate_catalog(work,scope)
        report["original_source_sha256"]={p:digest(raw) for p,raw in originals.items()}
        report["candidates"]=[{k:v for k,v in c.items() if k not in ("old","new")} for c in catalog]
        if metadata_status!="CANDIDATE_CATALOG_ADMITTED":
            report["status"]=metadata_status
            return
        if not catalog:
            report["status"]="REJECTED_NO_ORIGINAL_QUALIFIED_PRIMITIVE_SITES"
            return
        failures={n for n,v in before.items() if v=="FAIL"}
        baseline_pass={n for n,v in before.items() if v=="PASS"}
        selected=[]
        for step in range(MAX_PARTS):
            if not failures:
                break
            options=[]
            for i,c in enumerate(catalog):
                if i in selected:
                    continue
                if len(report["trials"])>=MAX_TRIALS:
                    report["status"]="UNKNOWN_NATIVE_TRIAL_BUDGET"
                    return
                chosen=selected+[i]
                rendered=render_sources(originals,catalog,chosen)
                try:
                    patch_world(work,originals,rendered,task["author_test"])
                    trial=one_native(work,project,python,admission["protected_nodes"],out,
                                     "choice-%02d-%02d"%(step,i))
                    checked(trial,before)
                    failed={n for n,v in trial["verdicts"].items() if v=="FAIL"}
                    good={n for n,v in trial["verdicts"].items() if v=="PASS"}
                    record={"step":step,"index":i,"patch_sites":[catalog[x]["path"] for x in chosen],
                            "native":trial,"remaining_failures":sorted(failed),
                            "regressions":sorted(failed-failures)}
                    report["trials"].append(record)
                    if not failed-failures and len(failed)<len(failures) and baseline_pass.issubset(good):
                        options.append((len(failures-failed),sum(abs(catalog[z]["bytes_added"]) for z in chosen),i,failed))
                finally:
                    patch_world(work,originals,{},task["author_test"])
            if not options:
                report["status"]="REJECTED_NO_ADMISSIBLE_MONOTONE_ADDITIVE_REPAIR"
                return
            options.sort(key=lambda v:(-v[0],v[1],v[2]))
            winner=options[0]
            selected.append(winner[2])
            failures=winner[3]
            report["selected"].append({"index":winner[2],"remaining_failures":sorted(failures)})
        if failures:
            report["status"]="REJECTED_INCOMPLETE_COMPOSITION"
            return
        full=render_sources(originals,catalog,selected)
        patch_world(work,originals,full,task["author_test"])
        report["new_source_sha256"]={p:digest(raw) for p,raw in full.items()}
        repeated=[]
        for label in ("repair-protected-a","repair-protected-b"):
            trial=one_native(work,project,python,admission["protected_nodes"],out,label)
            checked(trial,before)
            repeated.append(trial)
        if not all(all(z=="PASS" for z in x["verdicts"].values()) for x in repeated):
            report["status"]="REJECTED_REPEATED_NATIVE_PROTECTED"
            return
        report["repeated_protected"]=repeated
        entire=one_native(work,project,python,admission["protected_nodes"],out,"full-author",True)
        report["full_author_suite"]=entire
        if (entire["exit"]!=0 or entire["counts"]["tests"]<=len(before)
            or any(entire["counts"][k] for k in ("failures","errors","skipped"))):
            report["status"]="REJECTED_FULL_AUTHOR_SUITE"
            return
        k=len(selected)
        assert k<=3
        passes={}
        for mask in range(1<<k):
            sites=[selected[j] for j in range(k) if mask&(1<<j)]
            rendered=render_sources(originals,catalog,sites)
            patch_world(work,originals,rendered,task["author_test"])
            trial=one_native(work,project,python,admission["protected_nodes"],out,"subset-%02d"%mask)
            checked(trial,before)
            report["subsets"][str(mask)]={"mask":mask,"original_candidate_indices":sites,
                "source_sha256":{p:digest(raw) for p,raw in rendered.items()},"native":trial}
            passes[mask]={n for n,v in trial["verdicts"].items() if v=="PASS"}
        assert report["subsets"]["0"]["native"]["verdicts"]==before
        assert len(passes[(1<<k)-1])==len(before)
        for mask in range(1<<k):
            for sup in range(1<<k):
                if mask&sup==mask:
                    assert passes[mask].issubset(passes[sup]),("MONOTONE_FAILURE",mask,sup)
        for i in range(k):
            assert len(passes[((1<<k)-1)^(1<<i)])<len(before),"NONNECESSARY_CONSTITUENT"
        patch_world(work,originals,{},task["author_test"])
        withdrawn=one_native(work,project,python,admission["protected_nodes"],out,"withdraw-all")
        checked(withdrawn,before)
        assert withdrawn["verdicts"]==before,"ORIGINAL_VECTOR_DID_NOT_RETURN"
        patch_world(work,originals,full,task["author_test"])
        restored=one_native(work,project,python,admission["protected_nodes"],out,"restore-all")
        checked(restored,before)
        assert all(z=="PASS" for z in restored["verdicts"].values())
        report["withdrawal"]=withdrawn
        report["restoration"]=restored
        diff="".join(
            "".join(difflib.unified_diff(originals[p].decode().splitlines(keepends=True),
                full[p].decode().splitlines(keepends=True),
                fromfile="original/"+p,tofile="generated/"+p))
            for p in sorted(full))
        (out/"GENERATED_EXPOSED_SOURCE_PATCH.diff").write_text(diff)
        report["generated_patch_sha256"]=digest(diff.encode())
        report["status"]="CANDIDATE_RETROSPECTIVE_MULTI_FILE_CAUSAL_NATIVE_COMPOSITION"
    except Exception as exc:
        report["status"]="UNKNOWN_NATIVE_APPARATUS"
        report["error"]=type(exc).__name__+": "+str(exc)[:800]
        report["traceback_tail"]=traceback.format_exc(limit=7)[-1700:]
    finally:
        if work is not None and originals is not None and task is not None:
            for path,raw in originals.items():
                (work/path).write_bytes(raw)
        report["wall_seconds"]=round(time.monotonic()-start,3)
        report["G2"]="UNKNOWN"
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print(json.dumps({k:report.get(k) for k in
            ("status","epistemic","G2","wall_seconds")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_import_scope_composition_v1.py FRESH_OUTPUT")
    main(Path(sys.argv[1]).resolve())
