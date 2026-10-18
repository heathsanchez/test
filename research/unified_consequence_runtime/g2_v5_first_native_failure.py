#!/usr/bin/env python3
"""Pre-registered deterministic first-NATIVE-FAIL admission, not G2 learning.

Reads exclusively the 5 TRAINING roles of the Git-frozen V2 manifest, in order.
The separate FUTURE source is never cloned, downloaded, tested, or opened.
"""
import ast,hashlib,json,os,pathlib,subprocess,sys,time,traceback,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
ROLE_PATH=U+"G2_OBSERVATION_CHOICE_V5_ROLE_FREEZE.json"
ROLE_COMMIT="d96833fa8a41b4e5b67d5a9498ee1b1607c476e2"
SOURCE_PROG=U+"g2_v5_first_native_failure.py"
TIMEOUT=120

def call(argv,cwd=None,timeout=180,env=None):
    st=time.monotonic()
    p=subprocess.run([str(x) for x in argv],cwd=cwd,stdout=subprocess.PIPE,
       stderr=subprocess.PIPE,text=True,timeout=timeout,env=env)
    return {"returncode":p.returncode,"stdout_tail":p.stdout[-2500:],
       "stderr_tail":p.stderr[-2500:],"elapsed_seconds":round(time.monotonic()-st,4)}

def git(repo,*args):
    p=subprocess.run(["git","-C",str(repo),*args],capture_output=True,text=True,timeout=55)
    if p.returncode:raise RuntimeError("GIT_"+str(args[:2])+":"+p.stderr[-500:])
    return p.stdout.strip()
def checksum(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def tests(raw):
    tree=ast.parse(raw)
    names={}
    def recurse(nodes,prefix):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test_"):
                names["::".join(prefix+[n.name])]=ast.dump(n,include_attributes=False)
            elif isinstance(n,ast.ClassDef) and n.name.startswith("Test"):
                recurse(n.body,prefix+[n.name])
    recurse(tree.body,[])
    return names
def select_protected(base,head,path):
    a=tests(base);b=tests(head)
    return [path+"::"+n for n in sorted(b) if a.get(n)!=b[n]]
def junit(path):
    if not path.is_file():return {"tests":0,"failures":0,"errors":1,"skipped":0}
    root=ET.parse(path).getroot()
    cases=list(root.iter("testcase"))
    return {"tests":len(cases),
        "failures":sum(bool(list(c.iter("failure"))) for c in cases),
        "errors":sum(bool(list(c.iter("error"))) for c in cases),
        "skipped":sum(bool(list(c.iter("skipped"))) for c in cases)}
def pkg_install(env_py,repo,rec,output):
    pip=[str(env_py),"-m","pip","install","--no-input","--disable-pip-version-check"]
    logs=[]
    first=call(pip+["pip==25.3"],timeout=90)
    logs.append({"step":"pin-pip",**first})
    if first["returncode"]:return "UNKNOWN_PIP_INSTALL",logs
    second=call(pip+["-e",str(repo)],timeout=130)
    logs.append({"step":"editable-original",**second})
    if second["returncode"]:return "UNKNOWN_EDITABLE_INSTALL",logs
    # Frozen source-authored test dependency precedence, no target-specific resolver.
    import tomllib
    p=repo/"pyproject.toml"
    spec=tomllib.loads(p.read_text()) if p.exists() else {}
    groups=spec.get("dependency-groups",{})
    extras=spec.get("project",{}).get("optional-dependencies",{})
    supp=[]
    label="NONE"
    if "test" in groups:label="GROUP:test";supp=["--group",str(p)+":test"]
    elif "tests" in groups:label="GROUP:tests";supp=["--group",str(p)+":tests"]
    elif "test" in extras:label="EXTRA:test";supp=["-e",str(repo)+"[test]"]
    elif "tests" in extras:label="EXTRA:tests";supp=["-e",str(repo)+"[tests]"]
    elif "dev" in extras:label="EXTRA:dev";supp=["-e",str(repo)+"[dev]"]
    elif (repo/"test-requirements.txt").is_file():
        label="FILE:test-requirements.txt";supp=["-r",str(repo/"test-requirements.txt")]
    elif (repo/"requirements-test.txt").is_file():
        label="FILE:requirements-test.txt";supp=["-r",str(repo/"requirements-test.txt")]
    rec["test_supplement"]=label
    if supp:
        third=call(pip+supp,timeout=150)
        logs.append({"step":"original-authored-test-supplement",**third})
        if third["returncode"]:return "UNKNOWN_TEST_DEPENDENCIES",logs
    fixed=call(pip+["pytest==9.1.1","pytest-cov==7.0.0"],timeout=90)
    logs.append({"step":"pinned-native-oracle",**fixed})
    if fixed["returncode"]:return "UNKNOWN_PYTEST_INSTALL",logs
    check=call([str(env_py),"-m","pip","check"],timeout=45)
    logs.append({"step":"pip-check",**check})
    if check["returncode"]:return "UNKNOWN_DEPENDENCY_CONFLICT",logs
    freeze=call([str(env_py),"-m","pip","freeze"],timeout=35)
    (output/"PIP_FREEZE.txt").write_text(freeze.get("stdout_tail",""))
    return "ENV_ADMITTED",logs

def one(task,idx,dest):
    rec={"repo":task["repo"],"pr":task["number"],"order":idx,
      "status":"UNKNOWN_NOT_EXECUTED","future_source":"SEALED_UNOPENED","G2":"UNKNOWN"}
    dest.mkdir()
    try:
        work=pathlib.Path("/tmp/g2-pool-original-"+str(idx))
        env=pathlib.Path("/tmp/g2-pool-venv-"+str(idx))
        if work.exists() or env.exists():raise RuntimeError("STALE_ISOLATION_DIR")
        call(["git","init","-q",str(work)],timeout=35)
        git(work,"remote","add","upstream","https://github.com/"+task["repo"]+".git")
        for sha in (task["base"],task["author_head"]):
            p=call(["git","-C",str(work),"fetch","--quiet","--depth=1",
                "--filter=blob:none","--no-tags","upstream",sha],timeout=120)
            if p["returncode"]:raise RuntimeError("GIT_FETCH_SOURCE_FAILED:"+p["stderr_tail"])
        git(work,"checkout","--quiet","--detach",task["base"])
        if git(work,"rev-parse","HEAD")!=task["base"]:raise RuntimeError("WRONG_BASE")
        if git(work,"status","--porcelain"):raise RuntimeError("DIRTY_BASE")
        test=task["author_test"]
        base_bytes=subprocess.check_output(["git","-C",str(work),"show",task["base"]+":"+test],timeout=40)
        head_bytes=subprocess.check_output(["git","-C",str(work),"show",task["author_head"]+":"+test],timeout=40)
        # Verify blobs against the actual pinned HEAD tree, not uncontrolled text.
        oid=git(work,"rev-parse",task["author_head"]+":"+test)
        full_oid=subprocess.check_output(["git","-C",str(work),"hash-object","--stdin"],input=head_bytes,timeout=30).decode().strip()
        if oid!=full_oid:raise RuntimeError("AUTHOR_TEST_BLOB_INTEGRITY_FAILED")
        prot=select_protected(base_bytes,head_bytes,test)
        rec.update({"protected_nodes":prot,"base_test_sha256":hashlib.sha256(base_bytes).hexdigest(),
                    "head_test_sha256":hashlib.sha256(head_bytes).hexdigest(),
                    "head_test_git_blob":oid,"source_sha256":checksum(work/task["production"])})
        if not prot:
            rec["status"]="UNKNOWN_NO_MECHANICALLY_CHANGED_AUTHOR_TEST_NODES"
            return rec
        (work/test).write_bytes(head_bytes)
        if git(work,"diff","--name-only").splitlines()!=[test]:
            raise RuntimeError("OUTSIDE_AUTHOR_TEST_CHANGE")
        # Isolate every source-native admission from the others.
        v=call([sys.executable,"-m","venv",str(env)],timeout=60)
        if v["returncode"]:raise RuntimeError("VENV:"+v["stderr_tail"])
        py=env/"bin/python"
        state,logs=pkg_install(py,work,rec,dest)
        rec["provisioning"]=logs
        if state!="ENV_ADMITTED":
            rec["status"]=state
            return rec
        junit_path=dest/"native.xml"
        rr=call([str(py),"-m","pytest","-q","--junitxml="+str(junit_path),*prot],
                cwd=work,timeout=TIMEOUT,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        rec["native"]={**rr,"counts":junit(junit_path)}
        c=rec["native"]["counts"]
        if rr["returncode"]==1 and c["tests"]>0 and c["failures"]>=1 and c["errors"]==0 and c["skipped"]==0:
            rec["status"]="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
            rec["work_dir"]=str(work)
            rec["interpreter"]=str(py)
        elif c["errors"] or c["tests"]==0 or rr["returncode"] not in (0,1):
            rec["status"]="UNKNOWN_NATIVE_APPARATUS"
        elif c["skipped"]>0:
            rec["status"]="UNKNOWN_PROTECTED_SKIPS"
        elif c["failures"]==0:
            rec["status"]="NOT_ELIGIBLE_NO_PROTECTED_FAILURE"
        else:
            rec["status"]="UNKNOWN_NATIVE_TEST_CLASSIFICATION"
        return rec
    except Exception as exc:
        rec["status"]="UNKNOWN_NATIVE_ADMISSION_ERROR"
        rec["error"]=type(exc).__name__+": "+str(exc)[:950]
        rec["traceback_tail"]=traceback.format_exc(limit=5)[-1500:]
        return rec
    finally:
        (dest/"RESULT.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")

def main(dest):
    dest.mkdir(parents=True,exist_ok=False)
    frozen=(ROOT/ROLE_PATH).read_bytes()
    ref=subprocess.check_output(["git","-C",str(ROOT),"show",ROLE_COMMIT+":"+ROLE_PATH])
    assert frozen==ref,"ROLE_MANIFEST_CHANGED_AFTER_FREEZE"
    manifest=json.loads(ref)
    assert manifest["state"]=="FROZEN_BEFORE_ANY_TARGET_SOURCE_OR_NATIVE_EXECUTION"
    candidates=[x for x in manifest["roles"] if x["role"].startswith("TRAINING_")]
    assert len(candidates)==3 and len([x for x in manifest["roles"] if x["role"]=="SEALED_FUTURE"])==1
    records=[];selected=None;start=time.monotonic()
    for i,task in enumerate(candidates):
        if time.monotonic()-start>1200:
            records.append({"order":i,"repo":task["repo"],"status":"UNKNOWN_TOTAL_ADMISSION_BUDGET"})
            break
        row=one(task,i,dest/("admission-"+str(i).zfill(2)))
        records.append(row)
        (dest/"PROGRESS.json").write_text(json.dumps({"admissions":records,
                  "future":"SEALED_UNOPENED","G2":"UNKNOWN"},indent=2)+"\n")
        print("ADMISSION",i,task["repo"],row["status"],flush=True)
        if row["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            selected=row;break
    result={"schema":"G2_NATIVE_FIRST_AUTHENTIC_FAILURE_POOL_ADMISSION_V2",
       "state":"FIRST_ELIGIBLE_NATIVE_FAILURE_ONLY","admissions":records,"selected":selected,
       "method_training":"PENDING_ONLY_IF_SELECTED","future":"SEALED_UNOPENED",
       "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
       "G5":"UNKNOWN","G6":"UNKNOWN",
       "status":"QUALIFIED_TRAINING_FAILURE_FUTURE_SEALED" if selected else
                "UNKNOWN_NO_QUALIFIED_NATIVE_TRAINING_IN_FROZEN_POOL",
       "wall_seconds":round(time.monotonic()-start,4)}
    (dest/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("POOL_RESULT",json.dumps({k:result[k] for k in ("status","future","G2")}),flush=True)
    return result
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_pool_first_native_failure_v1.py FRESH_OUTPUT")
    main(pathlib.Path(sys.argv[1]).resolve())
