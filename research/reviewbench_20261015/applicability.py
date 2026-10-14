#!/usr/bin/env python3
"""Read-only ReviewBench coverage probe over the unchanged qualified AST scanner.
No project imports or native execution. Candidate != finding/warrant.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from qualified_20261015.mathgraph_predictive_consistency_20261015 import invariant_generator as gen

def cmd(root,*args):
    p=subprocess.run(["git",*args],cwd=root,capture_output=True,text=True,timeout=25)
    if p.returncode:
        raise RuntimeError("SOURCE_UNAVAILABLE: "+p.stderr[-160:])
    return p.stdout.strip()

def inspect(repo,base,head):
    result={"base":base,"head":head,"status":"UNKNOWN","ast_candidates":[]}
    if cmd(repo,"rev-parse","HEAD")!=head:
        result["status"]="UNKNOWN_WRONG_HEAD"
        return result
    with tempfile.TemporaryDirectory() as td:
        base_dir=Path(td)/"base"
        cmd(repo,"worktree","add","--detach",str(base_dir),base)
        try:
            if cmd(base_dir,"rev-parse","HEAD")!=base:
                result["status"]="UNKNOWN_WRONG_BASE"
            else:
                pair={"base":base_dir,"head":repo}
                sources={"base":base,"head":head}
                candidates=gen.synthesize_candidates(repo,pair,sources)
                result["status"]="CANDIDATE_AST_SCAN_ONLY"
                result["ast_candidates"]=[
                    {"file":c["file"],"class":c["class"],"method":c["method"],
                     "line":c["source_range"][0]} for c in candidates[:30]
                ]
                result["candidate_count"]=len(candidates)
        finally:
            cmd(repo,"worktree","remove","--force",str(base_dir))
    return result

if __name__=="__main__":
    try:
        print(json.dumps(inspect(Path(sys.argv[1]),sys.argv[2],sys.argv[3]),sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status":"UNKNOWN_COVERAGE","error":type(exc).__name__}))
        sys.exit(2)
