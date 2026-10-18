#!/usr/bin/env python3
"""Versioned source-owned workspace admission adapter; not a new repair method.

No future author-fixed production is read. Original BASE production and exact
HEAD author-test overlay are preserved. Generic package-root resolution uses
source-authored pyproject and uv.lock, never a task-specific repair coordinate.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as original

MAX_PROVISION_SECONDS=600
MAX_NATIVE_SECONDS=160

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def sh(*args, cwd=None, timeout=180, env=None):
    start=time.monotonic()
    try:
        r=subprocess.run([str(v) for v in args],cwd=cwd,capture_output=True,text=True,
            timeout=timeout,env=env)
        return {"returncode":r.returncode,"stdout_tail":r.stdout[-2800:],
                "stderr_tail":r.stderr[-2800:],
                "seconds":round(time.monotonic()-start,3)}
    except subprocess.TimeoutExpired as e:
        return {"returncode":124,"stdout_tail":str(e.stdout or "")[-600:],
                "stderr_tail":"TIMEOUT:"+str(e.stderr or "")[-600:],
                "seconds":round(time.monotonic()-start,3)}

def source_owned_project(repo: Path, source: str, tests: str):
    """Select nearest common ancestor under original source owning pyproject."""
    src=(repo/source).resolve()
    test=(repo/tests).resolve()
    assert src.is_file() and test.is_file(),"ORIGINAL_PINNED_SOURCE_AND_TEST_REQUIRED"
    eligible=[]
    for parent in src.parents:
        if parent==repo.parent:
            break
        if (parent/"pyproject.toml").is_file() and (parent/"uv.lock").is_file():
            if test.is_relative_to(parent):
                eligible.append(parent)
    if not eligible:
        raise ValueError("UNKNOWN_SOURCE_OWNED_PROJECT_WITH_UV_LOCK")
    return eligible[0]

def one(task,idx,dest):
    rec={"repo":task["repo"],"pr":task["pr"],"order":idx,"status":"UNKNOWN_NOT_EXECUTED",
         "G2":"UNKNOWN","future_source":"OPENED_FOR_SOURCE_NATIVE_ORIGINAL",
         "environment_amendment":"SOURCE_OWNED_UV_WORKSPACE_V11"}
    dest.mkdir(parents=True,exist_ok=False)
    st=time.monotonic()
    try:
        work=Path("/tmp/g2-monorepo-original-"+str(idx))
        assert not work.exists(),"STALE_NATIVE_WORKTREE"
        first=sh("git","init","-q",work,timeout=35)
        assert first["returncode"]==0,first
        original.git(work,"remote","add","upstream","https://github.com/"+task["repo"]+".git")
        for revision in (task["base"],task["head"]):
            f=sh("git","-C",work,"fetch","--quiet","--depth=1",
                "--filter=blob:none","--no-tags","upstream",revision,timeout=150)
            if f["returncode"]!=0:
                raise RuntimeError("UNKNOWN_SOURCE_FETCH:"+f["stderr_tail"])
        original.git(work,"checkout","--quiet","--detach",task["base"])
        assert original.git(work,"rev-parse","HEAD")==task["base"],"WRONG_BASE"
        assert not original.git(work,"status","--porcelain"),"DIRTY_BASE"
        original_test=subprocess.check_output(["git","-C",str(work),"show",
            task["base"]+":"+task["author_test"]],timeout=45)
        author_test=subprocess.check_output(["git","-C",str(work),"show",
            task["head"]+":"+task["author_test"]],timeout=45)
        git_blob=original.git(work,"rev-parse",task["head"]+":"+task["author_test"])
        computed=subprocess.check_output(["git","-C",str(work),"hash-object","--stdin"],
            input=author_test,timeout=30).decode().strip()
        assert git_blob==computed,"AUTHOR_TEST_GIT_IDENTITY"
        protected=original.select_protected(original_test,author_test,task["author_test"])
        rec.update({"protected_nodes":protected,"base_test_sha256":sha(original_test),
            "head_test_sha256":sha(author_test),"head_test_git_blob":git_blob,
            "source_sha256":sha((work/task["production"]).read_bytes())})
        if not protected:
            rec["status"]="UNKNOWN_NO_CHANGED_AUTHOR_TEST_NODES"
            return rec
        (work/task["author_test"]).write_bytes(author_test)
        assert original.git(work,"diff","--name-only").splitlines()==[task["author_test"]], "OUTSIDE_TEST_OVERLAY"
        project=source_owned_project(work,task["production"],task["author_test"])
        rel=project.relative_to(work)
        rec["project_root"]=str(rel)
        rec["original_project_pyproject_sha256"]=sha((project/"pyproject.toml").read_bytes())
        rec["original_project_lock_sha256"]=sha((project/"uv.lock").read_bytes())
        version_file=project/".python-version"
        if version_file.is_file():
            assert version_file.read_text().strip().startswith("3.12"),"ORIGINAL_RUNTIME_NOT_PINNED_PY312"
        uv_check=sh("uv","--version",timeout=20)
        rec["uv_version"]=uv_check
        if uv_check["returncode"]!=0 or "0.11.1" not in uv_check["stdout_tail"]:
            rec["status"]="UNKNOWN_DECLARED_UV_TOOL_NOT_INSTALLED"
            return rec
        sync=sh("uv","sync","--locked","--group","dev",
            cwd=project,timeout=MAX_PROVISION_SECONDS,
            env={**os.environ,"UV_NO_PROGRESS":"1"})
        rec["source_declared_dependency_sync"]=sync
        if sync["returncode"]!=0:
            rec["status"]="UNKNOWN_ORIGINAL_LOCKED_DEPENDENCY_SYNC"
            return rec
        python=project/".venv/bin/python"
        assert python.is_file(),"SOURCE_OWNED_ENV_MISSING"
        env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
             "PYTHONPATH":str(project)+os.pathsep+os.environ.get("PYTHONPATH","")}
        rel_nodes=[str(Path(n.split("::")[0]).relative_to(rel))+"::"+"::".join(n.split("::")[1:])
                   for n in protected]
        junit=dest/"native.xml"
        native=sh(python,"-m","pytest","-q","--junitxml="+str(junit),*rel_nodes,
                cwd=project,timeout=MAX_NATIVE_SECONDS,env=env)
        rec["native"]={**native,"counts":original.junit(junit)}
        c=rec["native"]["counts"]
        if native["returncode"]==1 and c["tests"]>=1 and c["failures"]>=1 and c["errors"]==c["skipped"]==0:
            rec["status"]="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
            rec["work_dir"]=str(work)
            rec["interpreter"]=str(python)
        elif c["errors"] or c["tests"]==0 or native["returncode"] not in (0,1):
            rec["status"]="UNKNOWN_ORIGINAL_NATIVE_APPARATUS"
        elif c["skipped"]:
            rec["status"]="UNKNOWN_PROTECTED_SKIPS"
        else:
            rec["status"]="NOT_ELIGIBLE_NO_PROTECTED_FAILURE"
        return rec
    except Exception as err:
        rec["status"]="UNKNOWN_MONOREPO_ADMISSION_APPARATUS"
        rec["error"]=type(err).__name__+": "+str(err)[:750]
        rec["traceback_tail"]=traceback.format_exc(limit=7)[-1700:]
        return rec
    finally:
        rec["wall_seconds"]=round(time.monotonic()-st,3)
        (dest/"RESULT.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
        print("SOURCE_OWNED_NATIVE_ADMISSION",rec["status"],rec["repo"],flush=True)
