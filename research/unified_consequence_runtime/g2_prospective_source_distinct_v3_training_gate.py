#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, subprocess, sys, xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[2]
PROTOCOL="research/unified_consequence_runtime/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_PROTOCOL.json"
ROLE="research/unified_consequence_runtime/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_ROLE_FREEZE.json"
APP="research/unified_consequence_runtime/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_APPARATUS_V2.json"
PINS={
    PROTOCOL:"6b96a5dcb5fcdd449639ba09aa5fbd600da0524a",
    ROLE:"4c5670f489c9c435f1f47d706f6dca8373d6fa96",
    APP:"c9a3d984aa4d5c0658882617d14fcd961131decd",
}

from research.unified_consequence_runtime.g2_anyio_mutable_closure_equivalence_fix_v2 import scan_patterns

def git(repo,*args,raw=False):
    out=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return out if raw else out.decode().strip()

def sha(b): return hashlib.sha256(b).hexdigest()

def frozen(path,commit):
    live=(ROOT/path).read_bytes()
    old=git(ROOT,"show",commit+":"+path,raw=True)
    if live!=old: raise ValueError("FROZEN_FILE_CHANGED:"+path)
    return json.loads(old)

def junit(path):
    if not path.is_file():
        return {"tests":0,"failures":0,"errors":1,"skipped":0}
    root=ET.parse(path).getroot()
    suites=[root] if root.tag=="testsuite" else list(root.iter("testsuite"))
    return {k:sum(int(s.get(k,0)) for s in suites) for k in ("tests","failures","errors","skipped")}

def run_cmd(world,out,args):
    out.mkdir(parents=True,exist_ok=False)
    xml=out/"junit.xml"
    cmd=[sys.executable,"-m","pytest","-q","--junitxml="+str(xml),*args]
    proc=subprocess.run(cmd,cwd=world,capture_output=True,text=True,timeout=900)
    return {
        "command":cmd,
        "returncode":proc.returncode,
        "counts":junit(xml),
        "stdout_sha256":sha(proc.stdout.encode()),
        "stderr_sha256":sha(proc.stderr.encode()),
        "stdout_tail":proc.stdout[-2500:],
        "stderr_tail":proc.stderr[-2500:],
    }

def main(world,out,runtime):
    p=frozen(PROTOCOL,PINS[PROTOCOL]); roles=frozen(ROLE,PINS[ROLE]); app=frozen(APP,PINS[APP])
    world=world.resolve(strict=True); out=out.resolve(); out.mkdir(parents=True,exist_ok=False)
    t=roles["training"]
    if git(world,"rev-parse","HEAD")!=t["base"]: raise ValueError("WRONG_TRAINING_BASE")
    status_lines=[line for line in git(world,"status","--porcelain").splitlines() if line]
    changed_paths=[line[3:] for line in status_lines if len(line)>=4]
    if changed_paths != [t["author_tests"][0]]:
        raise ValueError("UNEXPECTED_TRAINING_WORKTREE:"+git(world,"status","--porcelain"))
    test=t["author_tests"][0]; prod=t["production"][0]
    expected_test=git(world,"show",t["head"]+":"+test,raw=True)
    if (world/test).read_bytes()!=expected_test: raise ValueError("AUTHOR_TEST_OVERLAY_DIFFERS")
    base_prod=git(world,"show",t["base"]+":"+prod,raw=True)
    if (world/prod).read_bytes()!=base_prod: raise ValueError("BASE_PRODUCTION_CHANGED")
    patterns=scan_patterns(prod,base_prod)
    runs=[]
    commands=[
      [test],
      ["--run-slow",test],
    ]
    for i,args in enumerate(commands):
        runs.append(run_cmd(world,out/f"native-{i}",args))
    failures=[r for r in runs if r["counts"]["tests"]>0 and r["counts"]["failures"]>0 and r["counts"]["errors"]==0]
    apparatus_unknown=any(r["counts"]["tests"]==0 or r["counts"]["errors"]>0 for r in runs)
    if failures and patterns:
        status="CANDIDATE_METHOD_APPLICABLE_NEEDS_LOCKED_EXECUTOR"
    elif failures and not patterns:
        status="REJECTED_METHOD_INAPPLICABLE_NO_MUTABLE_CLOSURE_PATTERN"
    elif apparatus_unknown:
        status="UNKNOWN_TRAINING_APPARATUS"
    else:
        status="UNKNOWN_NO_AUTHENTIC_TRAINING_PROTECTED_FAILURE"
    result={
      "schema":"UDM_G2_PROSPECTIVE_SOURCE_DISTINCT_V3_TRAINING_GATE",
      "status":status,
      "runtime":runtime,
      "training":t["repository"]+"#"+str(t["pr"]),
      "base":t["base"],"head_test_commit":t["head"],
      "production_path":prod,"production_sha256":sha(base_prod),
      "author_test_path":test,"author_test_sha256":sha(expected_test),
      "pattern_count":len(patterns),"patterns":patterns,
      "native_runs":runs,
      "authentic_failure_runs":len(failures),
      "future_repository":roles["heldout_future"]["repository"],
      "future_source":"UNOPENED",
      "future_native":"NOT_EXECUTED",
      "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
      "method_commit_parent":p["parent_training_authority"]["commit"],
    }
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:result[k] for k in ("status","runtime","pattern_count","authentic_failure_runs","future_source","G2")},sort_keys=True))
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("world",type=pathlib.Path);ap.add_argument("out",type=pathlib.Path);ap.add_argument("--runtime",required=True)
    a=ap.parse_args()
    try:r=main(a.world,a.out,a.runtime)
    except Exception as e:
        print(json.dumps({"status":"UNKNOWN_APPARATUS_EXCEPTION","reason":type(e).__name__+": "+str(e),"runtime":a.runtime,"G2":"UNKNOWN"}))
        raise
