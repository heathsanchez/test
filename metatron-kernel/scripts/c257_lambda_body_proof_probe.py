"""C257: bounded source-owned Lambda-body proof probe, never verdict authority."""
import argparse
import json
import os
import pathlib
import subprocess
import time
import zipfile
import c255_lambda_premise_replay as c255

def main():
    p=argparse.ArgumentParser()
    for key in ("archive","checker","flags","out"):
        p.add_argument("--"+key,required=True,type=pathlib.Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if c255.sha(a.archive.read_bytes()) != c255.ARCHIVE:
        raise ValueError("Official archived source bytes changed")
    hist=json.loads(a.flags.read_text())["flags"]
    if len(hist)!=24 or set(hist.values())!={"1"}:
        raise ValueError("Historical flag roster changed")
    with zipfile.ZipFile(a.archive) as z:
        manifest={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(manifest)!=212:raise ValueError("Unexpected official source cohort")
        source=z.read("inputs/good/perf/fueled-chain.ndjson")
        if c255.sha(source)!=c255.FUELED or c255.sha(source)!=manifest["good/perf/fueled-chain.ndjson"]["sha256"]:
            raise ValueError("Actual Fueled source changed")
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(hist)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in c255.EXTRAS})
    env.update({
        "NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE":"1",
        "NUCLEUS_C247_TYPED_PI_LOCAL_RETRY":"1",
        "NUCLEUS_C250_ZERO_DOMAIN_RETRY":"1",
        "NUCLEUS_C251_LITERAL_PI_VIEW":"1",
        "NUCLEUS_C252_ARGUMENT_PROOF_RETRY":"1",
        "NUCLEUS_C253_WIDEN_SCOPE":"1",
        "NUCLEUS_C254_ARG_ALLOWANCE_512":"1",
        "NUCLEUS_C255_LAMBDA_PREMISES":"1",
        "NUCLEUS_C256_BODY_FIRST_APP":"1",
        "NUCLEUS_C257_BODY_PROOF_PROBE":"1",
        "NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE":"1",
        "NUCLEUS_TRACE_DOWNSTREAM":"1",
        "NUCLEUS_C225_JUDGMENT_STEPS":"69632"
    })
    start=time.monotonic()
    proc=subprocess.run([str(a.checker)],input=source,env=env,
                        capture_output=True,timeout=180,check=False)
    log=proc.stderr.decode(errors="replace")
    (a.out/"c257-fueled.stderr").write_text(log)
    probes=[line for line in log.splitlines() if line.startswith("NUCLEUS_C257_BODY_PROBE:")]
    body=[line for line in log.splitlines() if line.startswith("NUCLEUS_C256_BODY:")]
    terminals=[line for line in log.splitlines() if line.startswith("NUCLEUS_DOWNSTREAM:")]
    if proc.returncode!=2 or terminals[-1:]!=[c255.TERM]:
        raise ValueError("Original conclusion/terminal changed")
    if not 1<=len(probes)<=2 or not body:
        raise ValueError("Required original body and proof probes were not observed")
    if any(":lambda=ExprId(4812):body=ExprId(4811):" not in line for line in probes):
        raise ValueError("Probe outside pinned Lambda owner")
    report={
        "state":"WARRANTED_BOUNDED_DIAGNOSTIC_IF_CI_SUCCESS",
        "proven_probes":sum(":candidate=Proven {" in line for line in probes),
        "unknown_probes":sum(":candidate=Unknown {" in line for line in probes),
        "probes":probes,
        "body_trace_first":body[:12],
        "whole_exit":proc.returncode,
        "whole_terminal":terminals[-1],
        "elapsed_s":round(time.monotonic()-start,3),
        "source_sha256":c255.FUELED,
        "archive_sha256":c255.ARCHIVE,
        "boundary":"Fresh 4096-step diagnostic check result not inserted into Nucleus",
    }
    (a.out/"c257-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("C257_SUMMARY "+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":main()
