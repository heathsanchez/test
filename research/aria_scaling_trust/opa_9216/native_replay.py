#!/usr/bin/env python3
"""Original OPA Go+Wasm evaluator differential replay. No upstream writes.
Author supplied fixes and tests. We don't infer correctness from a tool failure.
"""
import json, pathlib, subprocess, sys, time

BASE="37030a09d6088821a473f486fd75dd81ef394b74"
HEAD="d231b0381efd880597db736efdd74e6681000b54"
root=pathlib.Path(sys.argv[1]).resolve()
out=pathlib.Path(sys.argv[2]).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
cases=[
 {"case":"overlapping-key-pr-original","expr":'strings.replace_n({"info": "X", "anotherinfo": "Y"}, "anotherinfo")',
  "want":"Y"},
 {"case":"empty-key-insertion-pr-original","expr":'strings.replace_n({"": "X"}, "ab")',
  "want":"XaXbX"}
]
def run(cmd,cwd,seconds=40):
    start=time.perf_counter()
    try:
        r=subprocess.run(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,timeout=seconds,check=False)
        return {"exit":r.returncode,"stdout":r.stdout[-3000:].strip(),
                "stderr":r.stderr[-3000:].strip(),"seconds":round(time.perf_counter()-start,3),
                "timed_out":False}
    except subprocess.TimeoutExpired:
        return {"exit":None,"stdout":None,"stderr":"TIMED_OUT",
                "seconds":round(time.perf_counter()-start,3),"timed_out":True}
results={"schema":"metalogic.opa-heldout-native-replay.v1","original_external_repo":"open-policy-agent/opa",
         "source":{"base_sha":BASE,"head_sha":HEAD},"observations":[],
         "upstream_fixes_written_by":"ORIGINAL_UPSTREAM_AUTHOR","generated_repairs":False,
         "human_review_time":"NOT_MEASURED","authorization":"NONE"}
for version,subdir in [("base",root/"base"),("head",root/"head")]:
  sha=BASE if version=="base" else HEAD
  got=run(["git","rev-parse","HEAD"],subdir,10)
  if got["exit"]!=0 or got["stdout"]!=sha: raise RuntimeError("SOURCE_REVISION_MISMATCH:"+version)
  binpath=root/(version+"-opa")
  built=run(["go","build","-tags=opa_wasm","-o",str(binpath),"."],subdir,540)
  results.setdefault("build",{})[version]={
    "exit":built["exit"],"seconds":built["seconds"],"timed_out":built["timed_out"],
    "stderr_tail":built["stderr"][-1600:] if built["stderr"] else ""}
  if built["exit"]!=0:
    results["result"]="NATIVE_REPLAY_INFRASTRUCTURE_UNKNOWN"
    out.write_text(json.dumps(results,indent=2)+"\n")
    print("NATIVE_BUILD_NOT_QUALIFIED "+version+" "+str(built["stderr"])[-1000:],flush=True)
    sys.exit(2)
  for case in cases:
    for target in ["rego","wasm"]:
      # -t rego is the OPA native topdown evaluator; wasm uses original committed Wasm runtime.
      cmd=[str(binpath),"eval","-f","raw","-t",target,case["expr"]]
      observed=run(cmd,subdir,25)
      results["observations"].append({
        "revision":version,"sha":sha,"target":target,"case":case["case"],
        "expected_topdown":case["want"],"command":cmd[1:],
        **observed})
      print("OPA_NATIVE "+json.dumps({
        "rev":version,"target":target,"case":case["case"],
        "exit":observed["exit"],"stdout":observed["stdout"],
        "timeout":observed["timed_out"],"seconds":observed["seconds"]}),flush=True)

def get(rev,target,case):
 return next(a for a in results["observations"] if a["revision"]==rev and
             a["target"]==target and a["case"]==case)
def good(o,want):return o["exit"]==0 and o["stdout"].strip('"')==want
over=cases[0]
brego=get("base","rego",over["case"])
bwasm=get("base","wasm",over["case"])
hrego=get("head","rego",over["case"])
hwasm=get("head","wasm",over["case"])
# The specific source PR reports old wasm returned anotherX rather than Y.
base_mismatch=good(brego,"Y") and good(bwasm,"anotherX")
head_converges=good(hrego,"Y") and good(hwasm,"Y")
empty=cases[1]
e_top=get("head","rego",empty["case"])
e_wasm=get("head","wasm",empty["case"])
empty_head_converges=good(e_top,"XaXbX") and good(e_wasm,"XaXbX")
results["predetermined_oracle"]={
 "historical_wasm_mismatch_reproduced":base_mismatch,
 "original_head_runtime_parity_reproduced":head_converges,
 "empty_key_head_converges":empty_head_converges}
results["result"]=("WARRANTED_BOUNDED_ORIGINAL_NATIVE_MISMATCH_AND_FIX"
                   if all((base_mismatch,head_converges,empty_head_converges))
                   else "NATIVE_OBSERVATION_NOT_AS_PREDECLARED")
out.write_text(json.dumps(results,indent=2)+"\n")
print("OPA_NATIVE_FINAL "+results["result"])
# Fail the qualifier if the claimed positive result doesn't hold. Preserve artifact via always upload.
sys.exit(0 if results["result"]=="WARRANTED_BOUNDED_ORIGINAL_NATIVE_MISMATCH_AND_FIX" else 1)
