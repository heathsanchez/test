"""C242: diagnose the source-owned Pi-opening failure, no checker rule change.

The SHA-pinned Fueled original has a source Pi body Expr203 at Gamma 11.
We separate lack of local fuel from failed source/capture obligations without
treating either observation as proof of equality or acceptance.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile

ARCHIVE_SHA = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED_SHA = "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
TERM = "NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"
TRIAL = re.compile(r"^NUCLEUS_C242_PI_TRIAL:expr=203:depth=11:ctx_specific=yes:frame=(\d+):free=(\d+):allowance=(\d+):spent=(\d+):left=(\d+):safe=(true|false):class=(proven|no-fuel|capture-or-support)$")
CONTROL = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)
EXTRAS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)

def replay(binary, raw, env, output, label, timeout=180):
    start=time.monotonic()
    p=subprocess.run([str(binary)], input=raw, env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     timeout=timeout, check=False)
    log=p.stderr.decode(errors="replace")
    (output/(label+".stderr")).write_text(log)
    return {"case":label,"exit":p.returncode,
            "elapsed_s":round(time.monotonic()-start,3),
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "terminal_count":log.splitlines().count(TERM),
            "log":log}

def parse(log):
    found=[]
    for line in log.splitlines():
        if not line.startswith("NUCLEUS_C242_PI_TRIAL:"):
            continue
        m=TRIAL.fullmatch(line)
        if not m:raise ValueError("C242 malformed event: "+line[:150])
        frame,free,allowance,spent,left,safe,category=m.groups()
        d={"frame":int(frame),"free":int(free),"allowance":int(allowance),
           "spent":int(spent),"left":int(left),"safe":safe=="true","class":category}
        if d["spent"]>d["allowance"]:raise ValueError("Invalid fuel observation")
        if d["safe"] != (d["class"]=="proven"):raise ValueError("Category inconsistent")
        if (d["class"]=="no-fuel") != (d["allowance"]==0):
            raise ValueError("No-fuel distinction inconsistent")
        found.append(d)
    if not found:raise ValueError("No exact original Pi observation")
    return {"total":len(found),
            "classes":dict(Counter(e["class"] for e in found)),
            "last_trials":found[-15:],
            "first_trials":found[:15],
            "distinct_frames":len(set(e["frame"] for e in found)),
            "candidate_causal_obligation":"UNKNOWN until source-owning return path established"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--checker",type=Path,required=True)
    p.add_argument("--flags",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(exist_ok=True,parents=True)
    if hashlib.sha256(a.archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:
        raise ValueError("Original archive digest mismatch")
    flags=json.loads(a.flags.read_text())["flags"]
    if len(flags)!=24 or set(flags.values())!={"1"}:
        raise ValueError("Historical flags changed")
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"]="1"
    env["NUCLEUS_C242_PI_OPENING_CAUSE"]="1"
    env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
    with zipfile.ZipFile(a.archive) as z:
        previous={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(previous)!=212:raise ValueError("Unexpected source population")
        def source(case):
            b=z.read("inputs/"+case)
            if hashlib.sha256(b).hexdigest()!=previous[case]["sha256"]:
                raise ValueError("Source drift: "+case)
            return b
        fueled=source("good/perf/fueled-chain.ndjson")
        if hashlib.sha256(fueled).hexdigest()!=FUELED_SHA:
            raise ValueError("Wrong original Fueled")
        observed=[]
        for budget in (65536,69632):
            trial_env=env.copy()
            if budget!=65536:
                trial_env["NUCLEUS_C225_JUDGMENT_STEPS"]=str(budget)
                trial_env["NUCLEUS_TRACE_RIGID_TYPE_MISMATCH"]="1"
            result=replay(a.checker,fueled,trial_env,a.out,f"fueled_{budget}")
            if result["exit"]!=2 or result["terminal_count"]!=1:
                raise ValueError("Original judgment changed: "+str(result)[:200])
            stats=parse(result.pop("log"))
            result["budget"]=budget
            result["observation"]=stats
            observed.append(result)
            print("C242_FUELED",json.dumps(result,sort_keys=True),flush=True)
        controls=[]
        for case in CONTROL:
            b=source(case)
            r=replay(a.checker,b,env,a.out,
                "control_"+case.replace("/","_").removesuffix(".ndjson"),timeout=75)
            r.pop("log")
            r["source_case"]=case
            if r["exit"]!=previous[case]["expected"] or r["exit"]!=previous[case]["actual"] or r["exit"] not in (0,1):
                raise ValueError("Protected control changed "+str(r))
            controls.append(r)
        if len(controls)!=7:raise ValueError("Missing controls")
    report={"status":"WARRANTED_BOUNDED_ONLY_IF_GITHUB_GREEN",
            "source_archive_sha256":ARCHIVE_SHA,
            "fueled_source_sha256":FUELED_SHA,
            "kernel_judgment_change":False,
            "actual_original_acceptance":"UNKNOWN",
            "paired_originals":observed,
            "protected":controls}
    (a.out/"c242-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("C242_SUMMARY",json.dumps({
        "originals":[{"budget":r["budget"],"status":r["exit"],
                      "classes":r["observation"]["classes"],"count":r["observation"]["total"]}
                     for r in observed],
        "control_exits":[r["exit"] for r in controls]},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
