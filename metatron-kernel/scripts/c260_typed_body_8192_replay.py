"""C260: source-pinned opt-in 8192-unit typed Lambda body retry A/B."""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import time
import zipfile
import c255_lambda_premise_replay as c255

VALID_ORIGINALS=(
    "good/perf/fueled-chain.ndjson",
)
def run(checker,raw,env,out,name,seconds=180):
    t=time.monotonic()
    try:
        p=subprocess.run([str(checker)],input=raw,env=env,timeout=seconds,capture_output=True,check=False)
        log=p.stderr.decode(errors="replace")
        outcome=p.returncode
    except subprocess.TimeoutExpired as exc:
        log=(exc.stderr or b"").decode(errors="replace")
        outcome=124
    (out/(name+".stderr")).write_text(log)
    witnesses=[x for x in log.splitlines() if x.startswith("NUCLEUS_C258_BODY_RETRY:")]
    terminal=[x for x in log.splitlines() if x.startswith("NUCLEUS_DOWNSTREAM:")]
    return {"case":name,"exit":outcome,"elapsed_s":round(time.monotonic()-t,3),
            "proof_events":witnesses[:32],
            "proof_proven":sum(":candidate=Proven {" in x for x in witnesses),
            "terminal":terminal[-1:]}

def main():
    p=argparse.ArgumentParser()
    for key in ("archive","checker","flags","out"):
        p.add_argument("--"+key,type=pathlib.Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if c255.sha(a.archive.read_bytes())!=c255.ARCHIVE:
        raise ValueError("Official source archive identity mismatch")
    historical=json.loads(a.flags.read_text())["flags"]
    if len(historical)!=24 or set(historical.values())!={"1"}:
        raise ValueError("Historical feature roster changed")
    base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    base.update(historical)
    base.update({f"NUCLEUS_EXPERIMENTAL_{key}":"1" for key in c255.EXTRAS})
    base.update({
        "NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE":"1",
        "NUCLEUS_C247_TYPED_PI_LOCAL_RETRY":"1",
        "NUCLEUS_C250_ZERO_DOMAIN_RETRY":"1",
        "NUCLEUS_C251_LITERAL_PI_VIEW":"1",
        "NUCLEUS_C252_ARGUMENT_PROOF_RETRY":"1",
        "NUCLEUS_C253_WIDEN_SCOPE":"1",
        "NUCLEUS_C254_ARG_ALLOWANCE_512":"1",
        "NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE":"1",
        "NUCLEUS_C225_JUDGMENT_STEPS":"69632",
        "NUCLEUS_TRACE_DOWNSTREAM":"1",
    })
    with zipfile.ZipFile(a.archive) as z:
        manifest={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(manifest)!=212:raise ValueError("Expected original 212 source cases")
        def get(case):
            b=z.read("inputs/"+case)
            if c255.sha(b)!=manifest[case]["sha256"]:
                raise ValueError("Original source drift: "+case)
            return b
        if c255.sha(get(VALID_ORIGINALS[0]))!=c255.FUELED:
            raise ValueError("Wrong authentic Fueled export")
        examined=[]
        for case in VALID_ORIGINALS:
            if manifest[case]["expected"]!=0 or manifest[case]["actual"]!=2:
                raise ValueError("Six historical UNKNOWN census changed: "+case)
            b=get(case)
            for enabled in (False,True):
                env=base.copy()
                if enabled:
                    env["NUCLEUS_C258_FORMED_BODY_RETRY"]="1"
                    env["NUCLEUS_C258_TRACE"]="1"
                    env["NUCLEUS_C260_BODY_8192"]="1"
                result=run(a.checker,b,env,a.out,
                           case.replace("/","_").removesuffix(".ndjson")+f"_on{int(enabled)}")
                result.update({"original":case,"candidate_on":enabled,"source_sha256":c255.sha(b)})
                if (not enabled and result["exit"]!=2) or (enabled and result["exit"] not in (0,2)):
                    raise ValueError("Wrong original or invalid new verdict: "+str(result))
                examined.append(result)
                print("C260_ORIGINAL "+json.dumps({k:v for k,v in result.items() if k!="proof_events"},sort_keys=True),flush=True)
        protected=[]
        for case in c255.CONTROLS:
            b=get(case)
            if manifest[case]["actual"]!=manifest[case]["expected"]:
                raise ValueError("Historical protected control was not decisive")
            for enabled in (False,True):
                env=base.copy()
                if enabled:
                    env["NUCLEUS_C258_FORMED_BODY_RETRY"]="1"
                    env["NUCLEUS_C260_BODY_8192"]="1"
                result=run(a.checker,b,env,a.out,
                           case.replace("/","_").removesuffix(".ndjson")+f"_on{int(enabled)}",seconds=90)
                if result["exit"]!=manifest[case]["expected"]:
                    raise ValueError("Protected control verdict drift: "+str(result))
                protected.append({"case":case,"candidate_on":enabled,"exit":result["exit"]})
    gains=[r["original"] for r in examined if r["candidate_on"] and r["exit"]==0]
    report={"state":"CANDIDATE_8192_UNTIL_FULL_212_CI_AND_ORIGINAL_BOUNDARY",
            "archive_sha256":c255.ARCHIVE,
            "source_fueled_sha256":c255.FUELED,
            "originals":examined,
            "protected":protected,
            "original_accept_gains":gains,
            "original_accept_gain_count":len(gains),
            "protected_verdicts_unchanged":len(protected)==22,
            "note":"Opt-in independent formation-checked Lambda body retry. No official Arena or Mathlib qualification."}
    (a.out/"c260-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("C260_SUMMARY "+json.dumps({"originals":[(r["original"],r["candidate_on"],r["exit"],r["proof_proven"]) for r in examined],
           "protected":len(protected),"gains":gains},sort_keys=True),flush=True)
if __name__=="__main__": main()
