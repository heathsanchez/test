#!/usr/bin/env python3
"""Source-derived jq-compatible filter candidates from added Rust test literals.

A generic, intentionally small *human-written* lexical generator. Never claims
the strings it extracts implement a semantic theorem; validates with native
original compiled CLI and a separate source-immutable oracle. No domain-
specific reference to any filter, issue, bug, repository or operation name.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, subprocess, sys

FILTER_PREFIX = (".", "select(", "map(", "try ", "if ", "reduce ",
                 "has(", "getpath(", "split(", "startswith(", "contains(",
                 "first(", "last(", "length", "empty", ".[", ".[[")
RUST_STR = re.compile(r'r(#{0,4})"([^"\n]*?)"\1|(?<![A-Za-z0-9_])"((?:\\.|[^"\\\n])*)"', re.DOTALL)
DEFAULT_INPUTS = [None, True, False, 0, 1, -1, "", "a", [], [0], [1], [[]],
                  ["a"], [0,1], {}, {"a":1}, {"a":[]}, {"":1}]
MAX_FILTERS = 42
MAX_INPUTS = 11
MAX_DOMAIN = 462

def code_sha(path):
    raw=pathlib.Path(path).read_bytes()
    return hashlib.sha256(raw).hexdigest()

def exact_source(path,sha):
    r=subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],
      text=True,capture_output=True,check=False,timeout=10)
    if r.returncode or r.stdout.strip()!=sha:
        raise RuntimeError("ORIGINAL_SOURCE_PIN_MOVED")

def rust_literals(line):
    out=[]
    for m in RUST_STR.finditer(line):
        try:
            v=m.group(2) if m.group(2) is not None else json.loads('"'+m.group(3)+'"')
        except (ValueError,TypeError):
            continue
        if len(v)<=250 and v.strip(): out.append(v)
    return out

def eligible_filter(v):
    if len(v)>200 or "\n" in v or "://" in v:return False
    v=v.strip()
    return v.startswith(FILTER_PREFIX) and not v.startswith(("./","../"))

def collect(diff):
    filters,seen=set(),set()
    ordered=[]
    inputs=[]
    # Test source detection is filename-based, not target-PR- or operation-based.
    # Search altered or new test files only. Source with no test change => UNKNOWN.
    test_file=False
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            filename=line[6:]
            test_file=filename.endswith(".rs") and ("test" in filename.lower() or "spec" in filename.lower())
            continue
        if not test_file or not line.startswith("+") or line.startswith("+++"):
            continue
        for lit in rust_literals(line[1:]):
            if eligible_filter(lit) and lit not in seen:
                seen.add(lit);ordered.append(lit)
            try: candidate=json.loads(lit)
            except json.JSONDecodeError:continue
            if isinstance(candidate,(dict,list,str,int,bool)) or candidate is None:
                inputs.append(candidate)
    if not ordered:return {"filters":[],"inputs":[],"status":"UNKNOWN_NO_SOURCE_DERIVED_FILTER"}
    # Preserve actual appearance order in authored test source; don't optimize
    # after observing native outputs.
    candidates=[]
    for val in inputs + DEFAULT_INPUTS:
        token=json.dumps(val,sort_keys=True,ensure_ascii=False,separators=(",",":"))
        if token not in filters:
            filters.add(token);candidates.append(val)
    ordered=ordered[:MAX_FILTERS]
    # fixed bounded search, not success-selected. preserve empty/arrays ahead.
    cases=candidates[:MAX_INPUTS]
    if len(ordered)*len(cases)>MAX_DOMAIN:
        ordered=ordered[:MAX_DOMAIN//len(cases)]
    return {"filters":ordered,"inputs":cases,"status":"CANDIDATE_SOURCE_DERIVED_PROBES"}

def make_manifest(base,head,discovery):
    filters=discovery["filters"]; inputs=discovery["inputs"]
    if not filters:return {"status":"UNKNOWN_NO_SOURCE_DERIVED_FILTER"}
    return {
      "schema":"metalogic.cross-implementation-native-domain.v1",
      "name":"third-original-rust-test-derived-filter-differential",
      "sources":[{"name":"original_base","local_dir":str(base["dir"]),"sha":base["sha"]},
                 {"name":"original_head","local_dir":str(head["dir"]),"sha":head["sha"]}],
      "axes":[{"name":"filter","type":"literals","values":filters},
              {"name":"input","type":"literals","values":inputs}],
      "expression":{"stdin":"{{input}}\n","normalization":"json"},
      "timeout_seconds":2,
      "arms":[
        {"name":"reference","argv":["jq","-c","{{filter}}"]},
        {"name":"base","argv":["{{BIN}}/third-base","-c","{{filter}}"]},
        {"name":"head","argv":["{{BIN}}/third-head","-c","{{filter}}"]}],
      "derived_from":"ADDED_RUST_TEST_LITERALS_ONLY",
      "test_operation_authorship":"ORIGINAL_UPSTREAM_CONTRIBUTOR",
      "extractor_authorship":"HUMAN_WRITTEN_UNCHANGED",
      "no_per_target_filter_manifest":True
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base-dir",required=True)
    p.add_argument("--base-sha",required=True)
    p.add_argument("--head-dir",required=True)
    p.add_argument("--head-sha",required=True)
    p.add_argument("--manifest-out",required=True)
    p.add_argument("--discovery-out",required=True)
    args=p.parse_args()
    exact_source(args.base_dir,args.base_sha);exact_source(args.head_dir,args.head_sha)
    d=subprocess.run(["git","-C",args.head_dir,"diff",
      "--unified=0",args.base_sha,args.head_sha,"--","*.rs","**/*.rs"],
      check=True,timeout=30,capture_output=True,text=True).stdout
    discovery=collect(d)
    discovery["original_diff_sha256"]=hashlib.sha256(d.encode()).hexdigest()
    discovery["extractor_sha256"]=code_sha(__file__)
    discovery["original_source_sha"]={"base":args.base_sha,"head":args.head_sha}
    manifest=make_manifest({"dir":args.base_dir,"sha":args.base_sha},
                           {"dir":args.head_dir,"sha":args.head_sha},discovery)
    pathlib.Path(args.discovery_out).parent.mkdir(parents=True,exist_ok=True)
    pathlib.Path(args.discovery_out).write_text(json.dumps(discovery,indent=2,ensure_ascii=False)+"\n")
    pathlib.Path(args.manifest_out).write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    print("SOURCE_DERIVED "+json.dumps({"status":discovery["status"],
      "extracted_filter_count":len(discovery["filters"]),
      "bounded_input_count":len(discovery["inputs"]),
      "manifest_status":manifest.get("status","COMPLETE")}))
    if not discovery["filters"]:sys.exit(2)
