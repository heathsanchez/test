#!/usr/bin/env python3
"""V1.1 apparatus-only support for genuine author-added tests.

An original BASE may have no author test file at a precommitted HEAD path.
The HEAD must contain a true regular Git blob. In that case the original AST
test map is empty and the same upstream author head file is overlaid by
git intent-to-add, allowing original native pytest and source-diff verification.
No regex method, test oracle, frozen role or future edits are modified.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

from . import g2_pool_first_native_failure_v1 as original

SCHEMA="G2_THIRD_SOURCE_NEW_HEAD_AUTHOR_TEST_NATIVE_V11"
HEX40=re.compile(r"[0-9a-f]{40}\Z")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_blob_name(name):
    if not isinstance(name,str) or not (name.startswith("test/") or name.startswith("tests/")) or (
            not name.endswith(".py") or name.startswith("/") or "\\" in name or "\x00" in name
            or any(v in ("",".","..") for v in name.split("/"))):
        raise ValueError("UNKNOWN_NONCANONICAL_ORIGINAL_AUTHOR_TEST_PATH")
    return name


def run_git(root,*args,check=True):
    return subprocess.run(["git","-C",str(root),"--no-replace-objects",*args],
        capture_output=True,check=check,timeout=55)


def author_blobs(repo,base,head,path):
    checked_blob_name(path)
    if (not isinstance(base,str) or not HEX40.fullmatch(base) or
            not isinstance(head,str) or not HEX40.fullmatch(head)):
        raise ValueError("UNKNOWN_NOT_IMMUTABLE_SOURCE_SHA")
    for commit in (base,head):
        if run_git(repo,"cat-file","-e",commit+"^{commit}",check=False).returncode:
            raise ValueError("UNKNOWN_ORIGINAL_SOURCE_COMMIT_NOT_FOUND")
    def read(commit,allow_absent):
        mode=run_git(repo,"ls-tree",commit,"--",path).stdout.decode().strip()
        if not mode:
            if allow_absent:
                return None
            raise ValueError("UNKNOWN_AUTHOR_HEAD_TEST_NOT_FOUND")
        parts=mode.split()
        if len(parts)!=4 or parts[0] not in ("100644","100755") or parts[1]!="blob" or parts[-1]!=path:
            raise ValueError("UNKNOWN_AUTHOR_SOURCE_MODE_OR_KIND")
        b=run_git(repo,"show",commit+":"+path).stdout
        return b
    original=read(base,True)
    head_bytes=read(head,False)
    if original is None:
        return b"",head_bytes,"AUTHOR_HEAD_ADDED_TEST"
    return original,head_bytes,"AUTHOR_BASE_EXISTS"


def stage_author_overlay(repo,test,data,kind):
    checked_blob_name(test)
    if kind not in ("AUTHOR_HEAD_ADDED_TEST","AUTHOR_BASE_EXISTS"):
        raise ValueError("UNKNOWN_AUTHOR_OVERLAY_KIND")
    root=Path(repo)
    path=root/test
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink():
        raise ValueError("UNKNOWN_AUTHOR_TEST_SYMLINK_IN_STAGE")
    path.write_bytes(data)
    if kind=="AUTHOR_HEAD_ADDED_TEST":
        if run_git(repo,"ls-files","--error-unmatch",test,check=False).returncode==0:
            raise ValueError("UNKNOWN_AUTHOR_TEST_ALREADY_TRACKED_AT_BASE")
        run_git(repo,"add","-N","--",test)
    if sha(path.read_bytes())!=sha(data):
        raise ValueError("UNKNOWN_AUTHOR_HEAD_TEST_BYTES_CHANGED")
    changes=run_git(repo,"diff","--name-only").stdout.decode().strip().splitlines()
    if changes!=[test]:
        raise ValueError("UNKNOWN_OUTSIDE_AUTHOR_TEST_OVERLAY_DIFF")


def one(task,idx,dest):
    rec={"schema":SCHEMA,"repo":task["repo"],"pr":task["pr"],"order":idx,
      "status":"UNKNOWN_NOT_EXECUTED","future_source":"SEALED_UNOPENED","G2":"UNKNOWN"}
    dest.mkdir(parents=True,exist_ok=False)
    try:
        work=Path("/tmp/g2-third-v11-base-"+str(idx))
        env=Path("/tmp/g2-third-v11-env-"+str(idx))
        if work.exists() or env.exists():
            raise ValueError("UNKNOWN_REPLAYED_SOURCE_WORLD")
        clone=original.call(["git","init","-q",str(work)],timeout=35)
        if clone["returncode"]:
            raise ValueError("UNKNOWN_GIT_INIT:"+clone["stderr_tail"])
        original.git(work,"remote","add","upstream","https://github.com/"+task["repo"]+".git")
        for commit in (task["base"],task["head"]):
            x=original.call(["git","-C",str(work),"fetch","--quiet","--depth=1",
                 "--filter=blob:none","--no-tags","upstream",commit],timeout=120)
            if x["returncode"]:
                raise ValueError("UNKNOWN_ORIGINAL_GIT_FETCH:"+x["stderr_tail"][-240:])
        original.git(work,"checkout","-q","--detach",task["base"])
        if original.git(work,"rev-parse","HEAD")!=task["base"] or (
                original.git(work,"status","--porcelain")):
            raise ValueError("UNKNOWN_ORIGINAL_BASE_NOT_CLEAN")
        test=task["author_test"];base,head,kind=author_blobs(work,task["base"],task["head"],test)
        oid=original.git(work,"rev-parse",task["head"]+":"+test)
        got=subprocess.check_output(["git","-C",str(work),"hash-object","--stdin"],
                  input=head,timeout=30).decode().strip()
        if oid!=got:
            raise ValueError("UNKNOWN_AUTHOR_TEST_GIT_BLOB_IDENTITY")
        protected=original.select_protected(base,head,test)
        production=work/task["production"]
        if production.is_symlink() or not production.is_file():
            raise ValueError("UNKNOWN_ORIGINAL_PRODUCTION_NOT_REGULAR_FILE")
        content=production.read_bytes()
        prod_oid=original.git(work,"rev-parse",task["base"]+":"+task["production"])
        actual_oid=subprocess.check_output(["git","-C",str(work),"hash-object","--stdin"],
                  input=content,timeout=30).decode().strip()
        if prod_oid!=actual_oid:
            raise ValueError("UNKNOWN_SOURCE_PRODUCTION_NOT_BASE_OWNED")
        rec.update({"protected_nodes":protected,"base_test_sha256":sha(base),
                 "head_test_sha256":sha(head),"head_test_git_blob":oid,
                 "source_sha256":sha(content),"author_test_kind":kind,
                 "test_profile":"ORIGINAL_OWNER_UNCHANGED"})
        if not protected:
            rec["status"]="UNKNOWN_NO_MECHANICALLY_CHANGED_AUTHOR_TEST_NODES"
            return rec
        stage_author_overlay(work,test,head,kind)
        create=original.call([sys.executable,"-m","venv",str(env)],timeout=60)
        if create["returncode"]:
            raise ValueError("UNKNOWN_NATIVE_VENV_CREATION")
        py=env/"bin/python"
        status,logs=original.pkg_install(py,work,rec,dest)
        rec["provisioning"]=logs
        if status!="ENV_ADMITTED":
            rec["status"]=status
            return rec
        junit=dest/"native.xml"
        attempt=original.call([str(py),"-m","pytest","-q",
                   "--junitxml="+str(junit),*protected],
                   cwd=work,timeout=120,
                   env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        rec["native"]={**attempt,"counts":original.junit(junit)}
        actual=rec["native"]["counts"]
        if (attempt["returncode"]==1 and actual["tests"]>0 and
                actual["failures"]>0 and actual["errors"]==0 and actual["skipped"]==0):
            rec["status"]="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
            rec["work_dir"]=str(work)
            rec["interpreter"]=str(py)
        elif actual["errors"]>0 or actual["tests"]==0 or attempt["returncode"] not in (0,1):
            rec["status"]="UNKNOWN_NATIVE_APPARATUS"
        elif actual["skipped"]>0:
            rec["status"]="UNKNOWN_PROTECTED_SKIPPED_CASE"
        elif actual["failures"]==0:
            rec["status"]="NOT_ELIGIBLE_NO_PROTECTED_FAILURE"
        else:
            rec["status"]="UNKNOWN_PROTECTED_NATIVE_OUTCOME"
        return rec
    except Exception as e:
        rec["status"]="UNKNOWN_NATIVE_ADMISSION_ERROR"
        rec["error"]=type(e).__name__+":"+str(e)[:950]
        rec["traceback_tail"]=traceback.format_exc(limit=5)[-1700:]
        return rec
    finally:
        (dest/"RESULT.json").write_text(json.dumps(rec,indent=2,sort_keys=True,default=str)+"\n")
